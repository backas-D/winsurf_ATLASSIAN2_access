"""Codex CLI agent wrapper.

Provides a local intermediate layer between the user and OpenAI Codex CLI.
The agent interprets natural-language messages, decides which tool to call,
and returns a structured response.  When the Codex CLI binary is not
available the module falls back to the OpenAI Chat Completions API with
function-calling so that the same tool definitions are honoured.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from openai import OpenAI

from backend import AppConfig

BASE_DIR = Path(__file__).resolve().parent
TOOLS_PATH = BASE_DIR / "codex_tools.json"

SYSTEM_PROMPT = """\
당신은 Atlassian 제품(Jira, Confluence)과 문서형 자료(사양서, 법규, 메일)를 \
분석하는 AI 어시스턴트입니다.

주요 역할:
1. Jira 이슈 검색, 조회, 요약, 분석
2. Confluence 페이지 검색, 조회, 요약, 분석
3. 업로드된 문서(사양서/법규/메일)에서 관련 내용 검색 및 답변
4. 외부 Confluence URL 내용 크롤링 및 분석
5. 복합 질의 (여러 소스를 결합한 분석)

응답 규칙:
- 간결하고 명확하게 한국어로 답변
- 문서 기반 답변 시 반드시 출처(문서명, 버전, 조문/절 등)를 표시
- 근거가 부족하면 "근거 부족"이라고 솔직하게 답변
- 법규는 시행일을, 메일은 발신자/시각을, 사양서는 버전/절을 함께 표시
"""


def _load_tools() -> list[dict[str, Any]]:
    """Load tool definitions from codex_tools.json."""
    if TOOLS_PATH.exists():
        return json.loads(TOOLS_PATH.read_text(encoding="utf-8"))
    return []


def _tools_as_openai_functions(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert our tool definitions to OpenAI function-calling format."""
    functions = []
    for tool in tools:
        functions.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
            },
        })
    return functions


class CodexAgent:
    """Wrapper around the Codex CLI (or Chat Completions fallback)."""

    def __init__(self, config: AppConfig, tool_executor: "ToolExecutor | None" = None):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model or "gpt-4o-mini"
        self.tools = _load_tools()
        self.openai_functions = _tools_as_openai_functions(self.tools)
        self.tool_executor = tool_executor
        self.codex_available = shutil.which("codex") is not None
        self.conversation_history: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_message(
        self,
        user_message: str,
        vision_images: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Process a user message and return a structured response."""
        self.conversation_history.append({"role": "user", "content": user_message})

        if vision_images:
            result = self._process_via_chat_api(user_message, vision_images=vision_images)
        elif self.codex_available:
            result = self._process_via_codex_cli(user_message)
        else:
            result = self._process_via_chat_api(user_message)

        if result.get("success") and result.get("message"):
            self.conversation_history.append(
                {"role": "assistant", "content": result["message"]}
            )

        return result

    def clear_history(self) -> None:
        self.conversation_history = []

    # ------------------------------------------------------------------
    # Codex CLI path
    # ------------------------------------------------------------------

    def _process_via_codex_cli(self, user_message: str) -> dict[str, Any]:
        """Invoke `codex` CLI as a subprocess."""
        try:
            tools_arg = json.dumps(self.tools, ensure_ascii=False)

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(tools_arg)
                tools_file = tmp.name

            cmd = [
                "codex",
                "--model", self.model,
                "--tools-file", tools_file,
                "--quiet",
                user_message,
            ]

            env = {**os.environ, "OPENAI_API_KEY": self.config.openai_api_key}

            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, env=env
            )

            os.unlink(tools_file)

            if proc.returncode != 0:
                return self._process_via_chat_api(user_message)

            output = proc.stdout.strip()

            tool_calls = self._parse_tool_calls(output)
            if tool_calls and self.tool_executor:
                results = self._execute_tools(tool_calls)
                final = self._summarise_with_llm(user_message, tool_calls, results)
                return final

            return {
                "success": True,
                "mode": "codex_cli",
                "message": output,
                "intent": "general",
                "action_result": None,
            }

        except Exception as exc:
            return self._process_via_chat_api(user_message)

    # ------------------------------------------------------------------
    # Chat Completions fallback (function-calling)
    # ------------------------------------------------------------------

    def _process_via_chat_api(
        self,
        user_message: str,
        vision_images: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Use Chat Completions API with function-calling as fallback."""
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *self.conversation_history,
            ]

            if vision_images and messages and messages[-1].get("role") == "user":
                multimodal_content: list[dict[str, Any]] = [{"type": "text", "text": user_message}]
                for image in vision_images:
                    data_url = (image or {}).get("data_url", "")
                    if data_url:
                        multimodal_content.append(
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url},
                            }
                        )
                messages[-1] = {"role": "user", "content": multimodal_content}

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.openai_functions if self.openai_functions else None,
                tool_choice="auto" if self.openai_functions else None,
                temperature=0.7,
                max_completion_tokens=2000,
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                return self._handle_tool_calls(choice.message, messages)

            assistant_msg = choice.message.content or ""

            return {
                "success": True,
                "mode": "chat_api",
                "message": assistant_msg,
                "intent": "general",
                "action_result": None,
            }

        except Exception as exc:
            error_msg = str(exc)

            if "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                return self._fallback_rule_based(user_message)

            return {
                "success": False,
                "mode": "chat_api",
                "message": f"오류가 발생했습니다: {error_msg}\n\n💡 OpenAI API 키와 할당량을 확인해주세요.",
                "intent": "error",
                "action_result": None,
            }

    def _handle_tool_calls(
        self, assistant_message: Any, messages: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Execute tool calls requested by the model, then get final answer."""
        messages.append(assistant_message.model_dump())

        tool_results: list[dict[str, Any]] = []

        for tc in assistant_message.tool_calls:
            func_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            if self.tool_executor:
                output = self.tool_executor.execute(func_name, args)
            else:
                output = {"error": f"Tool executor not configured for {func_name}"}

            output_str = json.dumps(output, ensure_ascii=False)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": output_str,
            })
            tool_results.append({"tool": func_name, "args": args, "result": output})

        follow_up = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_completion_tokens=2000,
        )

        final_msg = follow_up.choices[0].message.content or ""

        action_result = None
        if len(tool_results) == 1:
            action_result = tool_results[0].get("result")

        return {
            "success": True,
            "mode": "codex_agent",
            "message": final_msg,
            "intent": tool_results[0]["tool"] if tool_results else "general",
            "action_result": action_result,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_tool_calls(self, output: str) -> list[dict[str, Any]] | None:
        """Try to extract structured tool calls from Codex CLI output."""
        try:
            data = json.loads(output)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "tool" in data:
                return [data]
        except json.JSONDecodeError:
            pass
        return None

    def _execute_tools(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        results = []
        for tc in tool_calls:
            name = tc.get("tool") or tc.get("name", "")
            args = tc.get("args") or tc.get("arguments", {})
            if self.tool_executor:
                output = self.tool_executor.execute(name, args)
            else:
                output = {"error": "No executor"}
            results.append({"tool": name, "result": output})
        return results

    def _summarise_with_llm(
        self,
        user_message: str,
        tool_calls: list[dict[str, Any]],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Ask the LLM to produce a final answer given tool results."""
        context = json.dumps(results, ensure_ascii=False, indent=2)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
            {
                "role": "assistant",
                "content": f"다음은 도구 실행 결과입니다:\n{context}\n\n위 결과를 바탕으로 사용자에게 답변하겠습니다.",
            },
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_completion_tokens=2000,
        )
        msg = response.choices[0].message.content or ""
        return {
            "success": True,
            "mode": "codex_cli",
            "message": msg,
            "intent": results[0]["tool"] if results else "general",
            "action_result": results[0].get("result") if len(results) == 1 else None,
        }

    def _fallback_rule_based(self, user_message: str) -> dict[str, Any]:
        """Minimal rule-based fallback when API quota is exhausted."""
        if self.tool_executor:
            import re

            msg_lower = user_message.lower()
            # Match project keys: IDA, J150, AO, G80, F2, GV60, etc.
            match_key = re.search(r"\b([A-Z][A-Z0-9]{1,9})\b", user_message)
            # Match Confluence page IDs in brackets [386584075] or standalone long numbers
            match_page_id = re.search(r"\[(\d{5,})\]", user_message) or re.search(r"pageId=(\d+)", user_message)
            # Match Confluence URLs
            match_url = re.search(r"(https?://\S*confluence\S*)", user_message, re.IGNORECASE)

            # --- Confluence page fetch (page ID or URL detected) ---
            if match_page_id or match_url:
                page_ref = match_page_id.group(1) if match_page_id else match_url.group(1)
                result = self.tool_executor.execute(
                    "fetch_confluence_page", {"page_id_or_url": page_ref}
                )
                if isinstance(result, dict) and not result.get("error"):
                    title = result.get("title", "")
                    atts = result.get("attachments", [])
                    if atts:
                        att_lines = "\n".join(
                            f"  - {a['title']} (v{a.get('version',1)}, {a.get('lastModified','')[:10]}, by {a.get('modifiedBy','')}) [{a.get('parentTitle','')}]"
                            for a in atts[:20]
                        )
                        msg = f"📄 **{title}** (ID: {result.get('id', page_ref)})\n\n📎 첨부 파일 {len(atts)}개 (하위 페이지 포함):\n{att_lines}"
                    else:
                        content_preview = (result.get("content", "") or "")[:500]
                        msg = f"📄 **{title}** (ID: {result.get('id', page_ref)})\n\n{content_preview}..."
                    msg += "\n\n⚠️ (API 할당량 초과로 간단한 응답 제공)"
                    return {
                        "success": True,
                        "mode": "rule_based",
                        "message": msg,
                        "intent": "fetch_confluence_page",
                        "action_result": result,
                    }
                else:
                    err = result.get("error", "알 수 없는 오류") if isinstance(result, dict) else str(result)
                    return {
                        "success": True,
                        "mode": "rule_based",
                        "message": f"페이지 조회 실패: {err}\n\n⚠️ (API 할당량 초과로 간단한 응답 제공)",
                        "intent": "fetch_confluence_page",
                        "action_result": None,
                    }

            # --- Jira search ---
            if any(w in msg_lower for w in ["jira", "이슈", "issue", "티켓", "프로젝트"]):
                if match_key:
                    result = self.tool_executor.execute(
                        "search_jira_issues", {"project_key": match_key.group(1)}
                    )
                    count = len(result) if isinstance(result, list) else 0
                    return {
                        "success": True,
                        "mode": "rule_based",
                        "message": f"{match_key.group(1)} 프로젝트의 이슈 {count}개를 찾았습니다.\n\n⚠️ (API 할당량 초과로 간단한 응답 제공)",
                        "intent": "search_jira_issues",
                        "action_result": {"type": "jira_issues", "data": result[:10] if isinstance(result, list) else [], "count": count},
                    }

            # --- Confluence search ---
            if any(w in msg_lower for w in ["confluence", "컨플", "페이지", "문서", "파일", "업로드", "첨부", "project"]):
                if match_key:
                    result = self.tool_executor.execute(
                        "search_confluence_pages", {"project_name": match_key.group(1)}
                    )
                    count = len(result) if isinstance(result, list) else 0
                    return {
                        "success": True,
                        "mode": "rule_based",
                        "message": f"{match_key.group(1)} 관련 페이지 {count}개를 찾았습니다.\n\n⚠️ (API 할당량 초과로 간단한 응답 제공)",
                        "intent": "search_confluence_pages",
                        "action_result": {"type": "confluence_pages", "data": result[:10] if isinstance(result, list) else [], "count": count},
                    }

        return {
            "success": True,
            "mode": "rule_based",
            "message": f"'{user_message}' 요청을 받았습니다. 프로젝트 Key나 스페이스 이름을 포함해서 다시 요청해주세요.\n\n⚠️ (API 할당량 초과로 간단한 응답 제공)",
            "intent": "general",
            "action_result": None,
        }


class ToolExecutor:
    """Executes tools on behalf of the Codex agent using local backend functions."""

    def __init__(self, config: AppConfig, rag_service: Any = None):
        self.config = config
        self.rag_service = rag_service

    def execute(self, tool_name: str, args: dict[str, Any]) -> Any:
        """Dispatch a tool call to the appropriate backend function."""
        from backend import find_confluence_pages, find_jira_issues

        try:
            if tool_name == "search_jira_issues":
                return find_jira_issues(args.get("project_key", ""), self.config)

            elif tool_name == "search_confluence_pages":
                return find_confluence_pages(args.get("project_name", ""), self.config)

            elif tool_name == "fetch_confluence_page":
                return self._fetch_confluence_page(args.get("page_id_or_url", ""))

            elif tool_name == "search_documents":
                if self.rag_service:
                    return self.rag_service.search(
                        query=args.get("query", ""),
                        source_types=args.get("source_types"),
                        limit=args.get("limit", 5),
                    )
                return {"error": "RAG service not configured"}

            elif tool_name == "upload_document":
                return {"error": "Document upload requires file data – use the web UI."}

            elif tool_name == "list_documents":
                if self.rag_service:
                    return self.rag_service.list_documents(
                        source_type=args.get("source_type"),
                        limit=args.get("limit", 20),
                    )
                return {"error": "RAG service not configured"}

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as exc:
            return {"error": str(exc)}

    def _fetch_confluence_page(self, page_id_or_url: str) -> dict[str, Any]:
        """Fetch a Confluence page by ID or URL."""
        import re
        import requests
        from backend import auth_headers

        page_id = page_id_or_url.strip()

        if not page_id.isdigit():
            patterns = [
                r"/pages/(\d+)/",
                r"pageId=(\d+)",
                r"/pages/(\d+)$",
            ]
            for pattern in patterns:
                match = re.search(pattern, page_id)
                if match:
                    page_id = match.group(1)
                    break
            else:
                return {"error": f"유효한 페이지 ID를 추출할 수 없습니다: {page_id_or_url}"}

        url = (
            f"{self.config.confluence_base_url}/rest/api/content/{page_id}"
            f"?expand=body.storage,version,space"
        )
        headers = auth_headers(self.config.confluence_pat)
        headers["Accept"] = "application/json"

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
        except Exception as exc:
            return {"error": f"Confluence 페이지 조회 실패: {exc}"}

        data = resp.json()
        raw_html = data.get("body", {}).get("storage", {}).get("value", "")

        try:
            from bs4 import BeautifulSoup

            text = BeautifulSoup(raw_html, "html.parser").get_text(separator="\n")
        except ImportError:
            import re as _re

            text = _re.sub(r"<[^>]+>", " ", raw_html)

        # Fetch attachments — CQL search across page + all descendants
        attachments: list[dict[str, Any]] = []
        try:
            cql = f"type=attachment AND ancestor={page_id}"
            cql_url = (
                f"{self.config.confluence_base_url}/rest/api/content/search"
                f"?cql={requests.utils.quote(cql)}&limit=100&expand=version,container"
            )
            cql_resp = requests.get(cql_url, headers=headers, timeout=20)
            cql_resp.raise_for_status()
            for att in cql_resp.json().get("results", []):
                ver = att.get("version", {})
                ext = att.get("extensions", {})
                container = att.get("container", {})
                attachments.append({
                    "title": att.get("title", ""),
                    "size": ext.get("fileSize", 0),
                    "mediaType": ext.get("mediaType", ""),
                    "parentTitle": container.get("title", ""),
                    "parentId": container.get("id", ""),
                    "version": ver.get("number", 1),
                    "lastModified": ver.get("when", ""),
                    "modifiedBy": ver.get("by", {}).get("displayName", ""),
                })
        except Exception:
            # Fallback: direct child attachments only
            try:
                att_url = (
                    f"{self.config.confluence_base_url}/rest/api/content/{page_id}"
                    f"/child/attachment?limit=50&expand=version"
                )
                att_resp = requests.get(att_url, headers=headers, timeout=15)
                att_resp.raise_for_status()
                for att in att_resp.json().get("results", []):
                    ver = att.get("version", {})
                    ext = att.get("extensions", {})
                    attachments.append({
                        "title": att.get("title", ""),
                        "size": ext.get("fileSize", 0),
                        "mediaType": ext.get("mediaType", ""),
                        "parentTitle": data.get("title", ""),
                        "parentId": page_id,
                        "version": ver.get("number", 1),
                        "lastModified": ver.get("when", ""),
                        "modifiedBy": ver.get("by", {}).get("displayName", ""),
                    })
            except Exception:
                pass
        # Sort by last modified descending
        attachments.sort(
            key=lambda a: a.get("lastModified", ""), reverse=True
        )

        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "space": data.get("space", {}).get("key", ""),
            "version": data.get("version", {}).get("number"),
            "content": text[:8000],
            "attachments": attachments,
            "url": f"{self.config.confluence_base_url}/pages/viewpage.action?pageId={page_id}",
        }
