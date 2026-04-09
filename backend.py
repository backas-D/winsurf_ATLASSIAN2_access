from __future__ import annotations

import json
import re
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, jsonify
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
DB_PATH = BASE_DIR / "project_data.db"
ENV_PATH = BASE_DIR / ".env"
TRAINING_OUTPUT_PATH = BASE_DIR / "training_engine.md"
TEST_RESULT_PATH = BASE_DIR / "test_result.md"
MCP_CONFIG_PATH = BASE_DIR / "mcp_config.json"

OEM_PROJECT_PREFIXES = {
    "KGM": ["J", "Q", "U", "Y", "O", "X"],
    "HMC": ["OV", "CL", "CD", "CV", "DL", "KA", "LW", "YB", "QV", "KY", 
            "GL", "JG", "JK", "JW", "JX", "RG", "RS", "SK", "SP", "RJ", 
            "QX", "QL", "PU", "PD", "NU", "NP", "SQ", "SU", "SX", "TM", 
            "YG", "YC", "TAM", "KS", "MQ", "NEON", "IG", "IK", "EG", 
            "FE", "HR", "AX", "BN", "BR"],
    "KMC": ["OV", "CL", "CD", "CV", "DL", "KA", "LW", "YB", "QV", "KY", 
            "GL", "JG", "JK", "JW", "JX", "RG", "RS", "SK", "SP", "RJ", 
            "QX", "QL", "PU", "PD", "NU", "NP", "SQ", "SU", "SX", "TM", 
            "YG", "YC", "TAM", "KS", "MQ", "NEON", "IG", "IK", "EG", 
            "FE", "HR", "AX", "BN", "BR"],
    "Genesis": ["GV", "G70", "G80", "G90", "GV60", "GV70", "GV80"],
    "STLA": ["F2", "F3", "F4"]
}

OEM_ROOT_PAGES = {
    "KGM": "53087142",
    "HMC": "48627901",
    "KMC": "330446288",
    "Genesis": "330446292",
    "STLA": "231411537"
}


@dataclass
class AppConfig:
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4"
    jira_base_url: str = ""
    jira_pat: str = ""
    confluence_base_url: str = ""
    confluence_pat: str = ""
    mcp_server_name: str = "ALM_MCP_STDIO"
    mcp_command: str = "node"
    mcp_dist_path: str = r"C:\Tools\alm-mcp-stdio\dist\index.js"


@dataclass
class ConfluenceNode:
    id: str
    title: str
    url: str
    children: list["ConfluenceNode"] = field(default_factory=list)


@dataclass
class JiraIssue:
    key: str
    summary: str
    status: str
    issue_type: str
    assignee: str
    url: str


@dataclass
class SearchState:
    project_name: str = ""
    selected_oem: str = "KGM"
    show_project_selector: bool = False
    discovered_projects: list[dict] = field(default_factory=list)
    confluence_tree: list[dict[str, Any]] = field(default_factory=list)
    jira_issues: list[dict[str, Any]] = field(default_factory=list)
    selected_confluence_page_id: str = ""
    training_output: str = ""
    flash_error: str = ""
    flash_success: str = ""


def load_env_values(env_path: Path = ENV_PATH) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def load_config() -> AppConfig:
    raw = load_env_values()
    
    valid_models = [
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", 
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
    ]
    model = raw.get("OPENAI_MODEL", "gpt-4o-mini")
    if model not in valid_models:
        model = "gpt-4o-mini"
    
    return AppConfig(
        openai_api_key=raw.get("OPENAI_API_KEY", ""),
        openai_model=model,
        jira_base_url=raw.get("JIRA_BASE_URL", "").rstrip("/"),
        jira_pat=raw.get("JIRA_PAT", "").strip(),
        confluence_base_url=raw.get("CONFLUENCE_BASE_URL", "").rstrip("/"),
        confluence_pat=raw.get("CONFLUENCE_PAT", "").strip(),
        mcp_dist_path=raw.get("ALM_MCP_STDIO_PATH", r"C:\Tools\alm-mcp-stdio\dist\index.js"),
    )


def ensure_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_key TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS training_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source_file TEXT NOT NULL,
                result_markdown TEXT NOT NULL
            )
            """
        )
        conn.commit()


def log_activity(action_type: str, target_type: str, target_key: str, payload: dict[str, Any]) -> None:
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO activity_log (created_at, action_type, target_type, target_key, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                action_type,
                target_type,
                target_key,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        conn.commit()


def get_recent_activity(limit: int = 10) -> list[dict[str, Any]]:
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT created_at, action_type, target_type, target_key, payload_json
            FROM activity_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "created_at": row["created_at"],
            "action_type": row["action_type"],
            "target_type": row["target_type"],
            "target_key": row["target_key"],
            "payload": json.loads(row["payload_json"]),
        }
        for row in rows
    ]


def auth_headers(token: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra:
        headers.update(extra)
    return headers


def request_json(
    url: str,
    headers: dict[str, str],
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    data: bytes | None = None,
    timeout: int = 20,
) -> Any:
    payload = data
    request_headers = dict(headers)
    if body is not None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    req = Request(url, headers=request_headers, method=method, data=payload)
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc
    return json.loads(raw) if raw else {}


def request_binary(url: str, headers: dict[str, str], data: bytes, content_type: str, method: str = "POST") -> Any:
    req = Request(url, headers={**headers, "Content-Type": content_type}, method=method, data=data)
    try:
        with urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc
    return json.loads(raw) if raw else {}


def jira_project_candidates(project_name: str) -> list[str]:
    normalized = project_name.strip().upper()
    candidates = [normalized]
    if normalized and "-" in normalized:
        candidates.append(normalized.split("-", 1)[0])
    return [candidate for candidate in candidates if candidate]


def normalize_project_tokens(project_name: str) -> list[str]:
    normalized = project_name.strip().upper()
    if not normalized:
        return []

    tokens = {normalized}
    tokens.update(part for part in re.split(r"[^A-Z0-9]+", normalized) if part)

    if "_" in normalized:
        tokens.add(normalized.split("_", 1)[-1])
    if "-" in normalized:
        tokens.add(normalized.split("-", 1)[-1])

    match = re.search(r"[A-Z]\d{3,}", normalized)
    if match:
        tokens.add(match.group(0))

    return sorted(token for token in tokens if token)


def score_confluence_candidate(project_name: str, page: dict[str, Any]) -> int:
    title = str(page.get("title", "")).upper()
    tokens = normalize_project_tokens(project_name)
    if not title or not tokens:
        return -1

    strong_tokens = [token for token in tokens if token == project_name.strip().upper() or any(ch.isdigit() for ch in token)]
    score = 0
    for token in strong_tokens:
        if title == token:
            score = max(score, 100)
        elif f" {token}" in title or f"{token} " in title or f"- {token}" in title or f"_{token}" in title:
            score = max(score, 90)
        elif token in title:
            score = max(score, 70)

    if any(token in title for token in strong_tokens):
        # Prefer shorter, more exact-looking titles over generic plan pages.
        score -= min(len(title), 80) // 10
        if "PROJECT PLAN" in title:
            score -= 10
        if "RELEASE NOTE" in title or "REQUIREMENT" in title or "DEVELOPMENT HISTORY" in title:
            score -= 20
        if re.search(r"\bRN\d+\b", title):
            score -= 20

    ancestors = page.get("ancestors", [])
    if isinstance(ancestors, list):
        score += max(0, 12 - len(ancestors) * 2)
    return score


def build_confluence_page_url(page: dict[str, Any], cfg: AppConfig) -> str:
    webui = page.get("_links", {}).get("webui", "")
    if isinstance(webui, str) and webui:
        return webui if webui.startswith("http") else f"{cfg.confluence_base_url}{webui}"

    page_id = str(page.get("id", ""))
    return f"{cfg.confluence_base_url}/pages/viewpage.action?pageId={page_id}" if page_id else cfg.confluence_base_url


def promote_to_confluence_project_root(project_name: str, page: dict[str, Any], cfg: AppConfig) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []

    ancestors = page.get("ancestors", [])
    if isinstance(ancestors, list):
        candidates.extend(ancestors)
    candidates.append(page)

    best_candidate = page
    best_score = score_confluence_candidate(project_name, page)

    for candidate in candidates:
        score = score_confluence_candidate(project_name, candidate)
        title = str(candidate.get("title", "")).upper()

        # Strongly prefer the highest matching ancestor that looks like a project container.
        if "PROJECT PLAN" in title or "RELEASE NOTE" in title or "REQUIREMENT" in title:
            score -= 15

        if score > best_score:
            best_score = score
            best_candidate = candidate

    return {
        "id": str(best_candidate.get("id", "")),
        "title": str(best_candidate.get("title", project_name)),
        "url": build_confluence_page_url(best_candidate, cfg),
    }


def pick_confluence_root(project_name: str, cfg: AppConfig) -> dict[str, Any] | None:
    if not cfg.confluence_base_url:
        raise RuntimeError("CONFLUENCE_BASE_URL is not configured in .env.")
    if not project_name.strip():
        raise RuntimeError("Project name is required.")
    if not cfg.confluence_pat:
        return {
            "id": "",
            "title": project_name.strip(),
            "url": f"{cfg.confluence_base_url}/dosearchsite.action?queryString={quote_plus(project_name.strip())}",
        }
    headers = auth_headers(cfg.confluence_pat)
    cql_candidates = [
        f'title="{project_name}" AND type=page ORDER BY lastmodified DESC',
        f'title~"{project_name}" AND type=page ORDER BY lastmodified DESC',
        f'text~"{project_name}" AND type=page ORDER BY lastmodified DESC',
    ]
    best_page: dict[str, Any] | None = None
    best_score = -1
    for cql in cql_candidates:
        payload = request_json(
            f"{cfg.confluence_base_url}/rest/api/content/search?{urlencode({'cql': cql, 'limit': 25, 'expand': 'ancestors'})}",
            headers,
        )
        results = payload.get("results", [])
        for page in results:
            score = score_confluence_candidate(project_name, page)
            if score > best_score:
                best_score = score
                best_page = page

    if best_page and best_score >= 70:
        return promote_to_confluence_project_root(project_name, best_page, cfg)
    return None


def fetch_confluence_children(page_id: str, cfg: AppConfig) -> list[dict[str, Any]]:
    if not page_id or not cfg.confluence_pat:
        return []
    headers = auth_headers(cfg.confluence_pat)
    start = 0
    items: list[dict[str, Any]] = []

    while True:
        payload = request_json(
            f"{cfg.confluence_base_url}/rest/api/content/{page_id}/child/page?limit=100&start={start}",
            headers,
        )
        results = payload.get("results", [])
        items.extend(results)
        if not results or len(results) < 100:
            break
        start += 100

    return items


def confluence_title_sort_key(title: str) -> tuple[int, str]:
    match = re.match(r"^\s*(\d+)[.) -]?\s*(.*)$", title)
    if match:
        return (int(match.group(1)), match.group(2).upper())
    return (999999, title.upper())


def build_confluence_tree_from_root(root: dict[str, Any], cfg: AppConfig) -> ConfluenceNode:
    root_node = ConfluenceNode(id=str(root.get("id", "")), title=str(root.get("title", "")), url=str(root.get("url", "")))
    if not root_node.id or not cfg.confluence_pat:
        return root_node

    def walk(node: ConfluenceNode) -> None:
        children = fetch_confluence_children(node.id, cfg)
        children.sort(key=lambda child: confluence_title_sort_key(str(child.get("title", ""))))
        for child in children:
            webui = child.get("_links", {}).get("webui", "")
            url = webui if str(webui).startswith("http") else f"{cfg.confluence_base_url}{webui}"
            child_node = ConfluenceNode(id=str(child.get("id", "")), title=str(child.get("title", "")), url=url)
            walk(child_node)
            node.children.append(child_node)

    walk(root_node)
    return root_node


def confluence_tree_to_dict(node: ConfluenceNode) -> dict[str, Any]:
    return {
        "id": node.id,
        "title": node.title,
        "url": node.url,
        "children": [confluence_tree_to_dict(child) for child in node.children],
    }


def find_related_projects(project_name: str, cfg: AppConfig) -> list[str]:
    if not cfg.confluence_base_url or not cfg.confluence_pat:
        return [project_name]
    
    headers = auth_headers(cfg.confluence_pat)
    cql = f'text~"{project_name}" AND type=page ORDER BY lastmodified DESC'
    
    try:
        payload = request_json(
            f"{cfg.confluence_base_url}/rest/api/content/search?{urlencode({'cql': cql, 'limit': 50})}",
            headers,
        )
        results = payload.get("results", [])
        
        related = set()
        patterns = [
            r'([A-Z]\d{3})',
            r'([A-Z]{2}\d{3})',
        ]
        
        for page in results:
            title = str(page.get("title", ""))
            for pattern in patterns:
                matches = re.findall(pattern, title)
                for match in matches:
                    if match and len(match) >= 3:
                        related.add(match)
        
        if project_name.upper() in related:
            related.discard(project_name.upper())
            related.add(project_name)
        
        return sorted(related) if related else [project_name]
        
    except Exception:
        return [project_name]


def find_confluence_pages(project_name: str, cfg: AppConfig) -> list[dict[str, Any]]:
    related_projects = find_related_projects(project_name, cfg)
    
    if len(related_projects) > 1:
        combined_name = ",".join(related_projects)
    else:
        combined_name = project_name
    
    root = pick_confluence_root(combined_name, cfg)
    if root is None:
        return []
    return [confluence_tree_to_dict(build_confluence_tree_from_root(root, cfg))]


def resolve_jira_project_key(project_name: str, cfg: AppConfig) -> str:
    if not cfg.jira_base_url:
        raise RuntimeError("JIRA_BASE_URL is not configured in .env.")
    if not project_name.strip():
        raise RuntimeError("Project name is required.")
    if not cfg.jira_pat:
        return jira_project_candidates(project_name)[0]
    payload = request_json(f"{cfg.jira_base_url}/rest/api/2/project", auth_headers(cfg.jira_pat))
    projects = payload if isinstance(payload, list) else []
    normalized = project_name.strip().upper()
    scored: list[tuple[int, str]] = []
    for project in projects:
        key = str(project.get("key", "")).strip()
        name = str(project.get("name", "")).strip()
        key_u = key.upper()
        name_u = name.upper()
        score = -1
        if normalized == key_u or normalized == name_u:
            score = 100
        elif key_u.endswith(normalized) or name_u.endswith(normalized):
            score = 90
        elif normalized in key_u or normalized in name_u:
            score = 70
        if score >= 0 and key:
            scored.append((score, key))
    if scored:
        scored.sort(key=lambda item: (-item[0], len(item[1])))
        return scored[0][1]
    return jira_project_candidates(project_name)[0]


def find_jira_issues(project_name: str, cfg: AppConfig) -> list[dict[str, Any]]:
    project_key = resolve_jira_project_key(project_name, cfg)
    if not cfg.jira_pat:
        board_url = f"{cfg.jira_base_url}/issues/?jql={quote_plus(f'project = {project_key} ORDER BY updated DESC')}"
        return [asdict(JiraIssue(key=project_key, summary="JIRA_PAT 미설정으로 검색 링크만 제공합니다.", status="CONFIG_REQUIRED", issue_type="Search", assignee="-", url=board_url))]
    params = urlencode({"jql": f"project = {project_key} ORDER BY updated DESC", "maxResults": 100, "fields": "summary,status,issuetype,assignee"})
    payload = request_json(f"{cfg.jira_base_url}/rest/api/2/search?{params}", auth_headers(cfg.jira_pat))
    issues: list[dict[str, Any]] = []
    for issue in payload.get("issues", []):
        fields = issue.get("fields", {})
        assignee = fields.get("assignee") or {}
        issues.append(
            asdict(
                JiraIssue(
                    key=str(issue.get("key", "")),
                    summary=str(fields.get("summary", "")),
                    status=str((fields.get("status") or {}).get("name", "")),
                    issue_type=str((fields.get("issuetype") or {}).get("name", "")),
                    assignee=str(assignee.get("displayName", "-")),
                    url=f"{cfg.jira_base_url}/browse/{issue.get('key', '')}",
                )
            )
        )
    return issues


def jira_create_issue(project_key: str, issue_type: str, summary: str, description: str, cfg: AppConfig) -> dict[str, Any]:
    if not cfg.jira_pat:
        raise RuntimeError("JIRA_PAT is required for issue creation.")
    payload = request_json(
        f"{cfg.jira_base_url}/rest/api/2/issue",
        auth_headers(cfg.jira_pat),
        method="POST",
        body={"fields": {"project": {"key": project_key}, "summary": summary, "description": description, "issuetype": {"name": issue_type}}},
    )
    log_activity("create", "jira_issue", payload.get("key", ""), payload)
    return payload


def jira_update_issue(issue_key: str, summary: str, description: str, cfg: AppConfig) -> None:
    if not cfg.jira_pat:
        raise RuntimeError("JIRA_PAT is required for issue updates.")
    fields: dict[str, Any] = {}
    if summary.strip():
        fields["summary"] = summary
    if description.strip():
        fields["description"] = description
    if not fields:
        raise RuntimeError("Provide at least summary or description to update.")
    request_json(f"{cfg.jira_base_url}/rest/api/2/issue/{issue_key}", auth_headers(cfg.jira_pat), method="PUT", body={"fields": fields})
    log_activity("update", "jira_issue", issue_key, fields)


def confluence_get_page(page_id: str, cfg: AppConfig) -> dict[str, Any]:
    if not cfg.confluence_pat:
        raise RuntimeError("CONFLUENCE_PAT is required for page updates.")
    return request_json(
        f"{cfg.confluence_base_url}/rest/api/content/{page_id}?expand=body.storage,version,space",
        auth_headers(cfg.confluence_pat),
    )


def upload_base64_image_to_confluence(page_id: str, base64_data: str, image_index: int, cfg: AppConfig) -> str:
    """Upload a Base64 image as a Confluence attachment and return the attachment URL"""
    import base64
    import io
    import datetime
    from werkzeug.datastructures import FileStorage
    
    try:
        # Extract the actual base64 data (remove data:image/...;base64, prefix)
        if ',' in base64_data:
            base64_data = base64_data.split(',', 1)[1]
        
        # Decode base64 to binary
        image_binary = base64.b64decode(base64_data)
        
        # Create a file-like object
        file_obj = io.BytesIO(image_binary)
        
        # Generate unique filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}_{image_index}.jpg"
        
        # Create FileStorage object
        file_storage = FileStorage(
            stream=file_obj,
            filename=filename,
            content_type='image/jpeg'
        )
        
        # Upload as attachment
        confluence_upload_attachment(page_id, file_storage, cfg)
        
        # Return Confluence image macro with proper namespace
        return f'<p><ac:image><ri:attachment ri:filename="{filename}"/></ac:image></p>'
    except Exception as e:
        print(f"Failed to upload image: {e}")
        import traceback
        traceback.print_exc()
        return ''


def sanitize_html_for_confluence(html: str, page_id: str, cfg: AppConfig, file_download_links: dict | None = None) -> str:
    """Sanitize HTML from Quill editor for Confluence XHTML compatibility"""
    import re
    
    # Extract and upload Base64 images
    image_index = 0
    def replace_base64_image(match):
        nonlocal image_index
        base64_data = match.group(1)
        image_index += 1
        confluence_image = upload_base64_image_to_confluence(page_id, base64_data, image_index, cfg)
        return confluence_image if confluence_image else ''
    
    # Replace Base64 images with Confluence image macros (handle both self-closing and regular img tags)
    html = re.sub(r'<img[^>]*src="(data:image/[^"]+)"[^>]*/?>', replace_base64_image, html)
    
    # Convert file attachment text to clickable Confluence download links
    # Pattern: 📎 <strong>filename.ext</strong> (123.45 KB)
    def normalize_filename(name):
        """파일명 정규화: 한글 등 비-ASCII 제거, 특수문자 정리"""
        # 비-ASCII 문자 제거 (한글 등)
        name = re.sub(r'[^\x00-\x7F]', '', name)
        # 영숫자, 마침표 외 모든 문자를 _로 치환
        name = re.sub(r'[^a-zA-Z0-9.]', '_', name)
        # 연속 _ 제거
        name = re.sub(r'_+', '_', name)
        # 마침표 앞뒤 _ 제거 (예: 1_.msg → 1.msg)
        name = re.sub(r'_\.', '.', name)
        name = re.sub(r'\._', '.', name)
        return name.strip('_').lower()
    
    def convert_file_link(match):
        filename = match.group(1)
        filesize = match.group(2)
        
        download_url = None
        if file_download_links:
            # 정확 매칭 시도
            if filename in file_download_links:
                download_url = file_download_links[filename]
            else:
                # 정규화 매칭 (한글이 제거된 Confluence 파일명과 비교)
                norm = normalize_filename(filename)
                for att_title, att_url in file_download_links.items():
                    if normalize_filename(att_title) == norm:
                        download_url = att_url
                        break
        
        if download_url:
            # XHTML에서 & → &amp; 이스케이프 필수
            safe_url = download_url.replace('&', '&amp;')
            return f'<p><strong>📎 첨부: <a href="{safe_url}">{filename}</a></strong> ({filesize})</p>'
        
        # Fallback: 텍스트로만 표시
        return f'<p><strong>📎 첨부: {filename}</strong> ({filesize})</p>'
    
    html = re.sub(r'<p>📎 <strong>([^<]+)</strong> \(([^)]+)\)</p>', convert_file_link, html)
    
    # Convert Quill font size classes to inline styles
    def convert_font_size(match):
        size_class = match.group(1)
        content = match.group(2)
        
        size_map = {
            'ql-size-small': 'font-size: 0.75em;',
            'ql-size-large': 'font-size: 1.5em;',
            'ql-size-huge': 'font-size: 2em;'
        }
        
        style = size_map.get(size_class, '')
        if style:
            return f'<span style="{style}">{content}</span>'
        return f'<span>{content}</span>'
    
    # Replace font size classes with inline styles
    html = re.sub(r'<span class="(ql-size-[^"]+)">([^<]*)</span>', convert_font_size, html)
    
    # Remove empty paragraphs that might cause issues
    html = re.sub(r'<p>\s*<br/?\s*>\s*</p>', '', html)
    html = re.sub(r'<p>\s*</p>', '', html)
    
    # Ensure self-closing tags are properly formatted
    html = re.sub(r'<br(?!\s*/?>)', '<br/>', html)
    html = re.sub(r'<br\s*>', '<br/>', html)
    
    return html.strip()


def confluence_update_page(page_id: str, append_text: str, title: str, cfg: AppConfig, file_download_links: dict | None = None) -> dict[str, Any]:
    page = confluence_get_page(page_id, cfg)
    next_version = int((page.get("version") or {}).get("number", 1)) + 1
    current_body = (((page.get("body") or {}).get("storage") or {}).get("value", "")) or ""
    
    if append_text.strip():
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Sanitize HTML from Quill editor and upload images
        sanitized_html = sanitize_html_for_confluence(append_text.strip(), page_id, cfg, file_download_links)
        
        new_content = f'\n<p><strong>[{timestamp}]</strong></p>\n{sanitized_html}\n'
        insert_pos = -1
        
        # Priority 1: Try to insert after [Software Release Note]
        markers = ['[Software Release Note]', '[SRR] Release Note']
        for marker in markers:
            if marker in current_body:
                marker_pos = current_body.find(marker)
                # Find the end of the line/paragraph containing the marker
                after_marker = current_body[marker_pos:]
                
                # Look for the next closing tag after the marker
                close_tags = ['</p>', '</h1>', '</h2>', '</h3>', '</h4>', '</strong>']
                min_pos = len(after_marker)
                for tag in close_tags:
                    pos = after_marker.find(tag)
                    if pos != -1 and pos < min_pos:
                        min_pos = pos + len(tag)
                
                insert_pos = marker_pos + min_pos
                break
        
        # Priority 2: Try to insert after the info macro (참고사항)
        if insert_pos == -1 and '<ac:structured-macro ac:name="info">' in current_body:
            start_pos = current_body.find('<ac:structured-macro ac:name="info">')
            if start_pos != -1:
                # Find the corresponding closing tag
                end_pos = current_body.find('</ac:structured-macro>', start_pos)
                if end_pos != -1:
                    insert_pos = end_pos + len('</ac:structured-macro>')
        
        # Priority 3: If no info macro, insert after page title (h1)
        if insert_pos == -1:
            h1_tags = ['</h1>', '</h2>']  # Try h1 first, then h2
            for tag in h1_tags:
                pos = current_body.find(tag)
                if pos != -1:
                    insert_pos = pos + len(tag)
                    break
        
        # Insert at determined position or append at end
        if insert_pos != -1:
            new_body = current_body[:insert_pos] + new_content + current_body[insert_pos:]
        else:
            # Fallback: append at the end
            new_body = f"{current_body}\n<p>{append_text.strip()}</p>"
    else:
        new_body = current_body
    
    page_title = title.strip() or page.get("title", "")
    payload = request_json(
        f"{cfg.confluence_base_url}/rest/api/content/{page_id}",
        auth_headers(cfg.confluence_pat),
        method="PUT",
        body={
            "id": page_id,
            "type": "page",
            "title": page_title,
            "space": {"key": ((page.get("space") or {}).get("key", ""))},
            "version": {"number": next_version},
            "body": {"storage": {"value": new_body, "representation": "storage"}},
        },
    )
    log_activity("update", "confluence_page", page_id, {"title": page_title, "append_text": append_text})
    return payload


def encode_multipart_formdata(file_storage: FileStorage) -> tuple[bytes, str]:
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    filename = secure_filename(file_storage.filename or "attachment.bin")
    content = file_storage.read()
    file_storage.stream.seek(0)
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return header + content + footer, f"multipart/form-data; boundary={boundary}"


def confluence_upload_attachment(page_id: str, file_storage: FileStorage, cfg: AppConfig) -> dict[str, Any]:
    if not cfg.confluence_pat:
        raise RuntimeError("CONFLUENCE_PAT is required for attachment upload.")
    body, content_type = encode_multipart_formdata(file_storage)
    payload = request_binary(
        f"{cfg.confluence_base_url}/rest/api/content/{page_id}/child/attachment",
        {**auth_headers(cfg.confluence_pat), "X-Atlassian-Token": "no-check"},
        body,
        content_type,
    )
    log_activity("upload", "confluence_attachment", page_id, {"filename": file_storage.filename})
    return payload


def heuristic_training_rules(markdown: str) -> str:
    pass_count = len(re.findall(r"\bpass\b", markdown, flags=re.IGNORECASE))
    fail_count = len(re.findall(r"\bfail\b", markdown, flags=re.IGNORECASE))
    blocked_count = len(re.findall(r"\bblocked\b", markdown, flags=re.IGNORECASE))
    defect_keywords = re.findall(r"(timeout|latency|crash|exception|error|mismatch|missing)", markdown, flags=re.IGNORECASE)
    top_issues = sorted({item.lower() for item in defect_keywords})
    rules = [
        "# Training Engine Rules",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- Source file: `{TEST_RESULT_PATH.name}`",
        f"- Pass count: {pass_count}",
        f"- Fail count: {fail_count}",
        f"- Blocked count: {blocked_count}",
        "",
        "## Suggested Rules",
        "- Prioritize repeated failure patterns before isolated failures.",
        "- Treat `Blocked` cases as environment issues unless the same step later fails functionally.",
        "- Require regression re-check for every keyword-based failure cluster.",
    ]
    if top_issues:
        rules.append(f"- Focus areas: {', '.join(top_issues)}")
    rules.append("- Tighten release gate because fail count currently exceeds pass count." if fail_count > pass_count else "- Keep current release gate but review failing scenarios before sign-off.")
    return "\n".join(rules) + "\n"


def generate_training_engine() -> str:
    ensure_storage()
    if not TEST_RESULT_PATH.exists():
        TEST_RESULT_PATH.write_text("# test_result.md\n\n- PASS: sample check\n- FAIL: sample timeout on login\n- BLOCKED: environment access pending\n", encoding="utf-8")
    markdown = TEST_RESULT_PATH.read_text(encoding="utf-8")
    result = heuristic_training_rules(markdown)
    TRAINING_OUTPUT_PATH.write_text(result, encoding="utf-8")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO training_runs (created_at, source_file, result_markdown) VALUES (?, ?, ?)", (datetime.now().isoformat(timespec="seconds"), TEST_RESULT_PATH.name, result))
        conn.commit()
    return result


def detect_oem_from_project_code(project_code: str) -> str | None:
    code_upper = project_code.strip().upper()
    
    for oem, prefixes in OEM_PROJECT_PREFIXES.items():
        sorted_prefixes = sorted(prefixes, key=len, reverse=True)
        for prefix in sorted_prefixes:
            if code_upper.startswith(prefix):
                return oem
    
    return None


def extract_project_code_from_title(title: str) -> str | None:
    title = title.strip()
    
    patterns = [
        r'^([A-Z]{2,4}(?:\s+\d+[A-Z]*)?(?:\.\d+)?(?:[A-Z]+)?)\s*\[',
        r'^([A-Z]{2,4}\d*(?:\s+[A-Z]+)?)\s+\[',
        r'^([A-Z]\d+[A-Z]*)\s*\[',
        r'^(F\dX?/F\dU?)\s*\[',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            return match.group(1).strip()
    
    return None


def is_valid_project_code(title: str) -> bool:
    title_upper = title.strip().upper()
    
    skip_keywords = ['COMPLETE', 'ARCHIVE', 'TEMPLATE', 'COMMON', 'HISTORY', 'DESIGN KOREA', 'VEHICLE DEV']
    if any(keyword in title_upper for keyword in skip_keywords):
        return False
    
    project_code = extract_project_code_from_title(title)
    return project_code is not None


def is_kgm_project_code(title: str) -> bool:
    title_stripped = title.strip()
    
    if any(ord(c) > 127 for c in title_stripped):
        return False
    
    title_upper = title_stripped.upper()
    
    patterns = [
        r'^[ACEJOQUXY]\d{2,4}[,\s]',
        r'^[ACEJOQUXY]\d{2,4}\s*\[',
        r'^FCM-\d+\s+[ACEJOQUXY]\d{2,4}',
        r'^[ACEJOQUXY]\d{2,4}\s+[ACEJOQUXY]\d{2,4}',
    ]
    
    matched = False
    for pattern in patterns:
        if re.search(pattern, title_upper):
            matched = True
            break
    
    if not matched:
        return False
    
    exclude_keywords = ['DAILY', 'TASK', 'REPORT', 'MEETING', 'REVIEW', 'TEMPLATE', 'REQUIREMENT', 'SAMPLE']
    if any(keyword in title_upper for keyword in exclude_keywords):
        return False
    
    return True


def get_oem_projects(oem: str, cfg: AppConfig) -> list[dict]:
    if not cfg.confluence_base_url or not cfg.confluence_pat:
        return []
    
    root_page_id = OEM_ROOT_PAGES.get(oem, "")
    if not root_page_id:
        return []
    
    try:
        if oem == "KGM":
            def collect_kgm_projects(page_id: str, depth: int = 0) -> list[dict]:
                if depth > 3:
                    return []
                
                try:
                    children = fetch_confluence_children(page_id, cfg)
                except Exception:
                    return []
                
                projects = []
                
                for child in children:
                    title = str(child.get("title", ""))
                    child_id = str(child.get("id", ""))
                    webui = child.get("_links", {}).get("webui", "")
                    url = webui if str(webui).startswith("http") else f"{cfg.confluence_base_url}{webui}"
                    
                    if is_kgm_project_code(title):
                        projects.append({
                            "id": child_id,
                            "title": title,
                            "url": url,
                            "oem": oem
                        })
                    
                    sub_projects = collect_kgm_projects(child_id, depth + 1)
                    projects.extend(sub_projects)
                
                return projects
            
            all_projects = collect_kgm_projects(root_page_id)
            
            seen = set()
            unique_projects = []
            for project in all_projects:
                if project["id"] not in seen:
                    seen.add(project["id"])
                    unique_projects.append(project)
            
            unique_projects.sort(key=lambda p: p["title"])
            return unique_projects
        
        else:
            children = fetch_confluence_children(root_page_id, cfg)
            
            projects = []
            for child in children:
                title = str(child.get("title", ""))
                child_id = str(child.get("id", ""))
                webui = child.get("_links", {}).get("webui", "")
                url = webui if str(webui).startswith("http") else f"{cfg.confluence_base_url}{webui}"
                
                projects.append({
                    "id": child_id,
                    "title": title,
                    "url": url,
                    "oem": oem
                })
            
            projects.sort(key=lambda p: p["title"])
            return projects
        
    except Exception as e:
        return []


def flatten_tree(tree_list: list[dict]) -> list[dict]:
    flat = []
    
    def walk(node):
        flat.append({
            "id": node.get("id"),
            "title": node.get("title"),
            "url": node.get("url")
        })
        for child in node.get("children", []):
            walk(child)
    
    for tree in tree_list:
        walk(tree)
    
    return flat


def extract_project_groups(tree_pages: list) -> list[dict]:
    flat_pages = flatten_tree(tree_pages)
    projects = {}
    
    for page in flat_pages:
        title = str(page.get("title", ""))
        
        patterns = [
            r"([A-Z]{3,6})_([A-Z]\d{3})",
            r"([A-Z]{3,6})\s+([A-Z]\d{3})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                project_code = match.group(1)
                
                if project_code not in projects:
                    projects[project_code] = {
                        "id": project_code,
                        "title": f"{project_code} 프로젝트",
                        "type": "Vehicle Platform",
                        "count": 0,
                        "pages": []
                    }
                
                projects[project_code]["pages"].append(page)
                projects[project_code]["count"] += 1
                break
    
    return list(projects.values())


def export_mcp_config(cfg: AppConfig) -> dict[str, Any]:
    payload = {"mcpServers": {cfg.mcp_server_name: {"command": cfg.mcp_command, "args": [cfg.mcp_dist_path]}}}
    MCP_CONFIG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


backend_bp = Blueprint("backend", __name__, url_prefix="/api")


@backend_bp.get("/state")
def api_state():
    cfg = load_config()
    return jsonify({"ok": True, "mcp_config_path": str(MCP_CONFIG_PATH), "jira_base_url": cfg.jira_base_url, "confluence_base_url": cfg.confluence_base_url, "recent_activity": get_recent_activity()})


@backend_bp.post("/training/generate")
def api_generate_training():
    return jsonify({"ok": True, "training_output": generate_training_engine()})


@backend_bp.post("/mcp/export")
def api_export_mcp():
    return jsonify({"ok": True, "config": export_mcp_config(load_config())})


@backend_bp.get("/recent-activity")
def api_recent_activity():
    from flask import request
    limit = request.args.get('limit', 10, type=int)
    limit = min(limit, 50)  # 최대 50개로 제한
    activities = get_recent_activity(limit)
    return jsonify({"ok": True, "activities": activities})
