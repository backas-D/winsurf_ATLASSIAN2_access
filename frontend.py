from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request, session, Response

from backend import (
    SearchState,
    build_confluence_tree_from_root,
    confluence_tree_to_dict,
    confluence_update_page,
    confluence_upload_attachment,
    detect_oem_from_project_code,
    export_mcp_config,
    extract_project_groups,
    find_confluence_pages,
    find_jira_issues,
    find_related_projects,
    generate_training_engine,
    get_oem_projects,
    jira_create_issue,
    jira_update_issue,
    load_config,
)
from chat_service import ChatService, CodexChatService

frontend_bp = Blueprint("frontend", __name__)

# USE_CODEX_AGENT=false in .env to rollback to legacy ChatService
_use_codex = True
chat_sessions: dict[str, ChatService | CodexChatService] = {}


def build_default_state() -> SearchState:
    return SearchState()


def render(state: SearchState):
    cfg = load_config()
    return render_template(
        "index.html",
        state=state,
        mcp_preview=export_mcp_config(cfg),
    )


@frontend_bp.get("/")
def index():
    state = build_default_state()
    
    tree_param = request.args.get("tree")
    if tree_param:
        try:
            import json
            tree_data = json.loads(tree_param)
            state.confluence_tree = [tree_data]
            state.selected_confluence_page_id = tree_data.get("id", "")
            state.flash_success = f"프로젝트 트리를 불러왔습니다: {tree_data.get('title', '')}"
        except Exception as e:
            state.flash_error = f"트리 데이터를 불러올 수 없습니다: {str(e)}"
    
    return render(state)


@frontend_bp.post("/search/confluence")
def search_confluence():
    state = build_default_state()
    cfg = load_config()
    
    state.project_name = (request.form.get("project_name") or "").strip()
    state.selected_oem = (request.form.get("oem") or "KGM").strip()
    
    detected_oem = detect_oem_from_project_code(state.project_name)
    if detected_oem:
        state.selected_oem = detected_oem
    
    try:
        related_projects = find_related_projects(state.project_name, cfg)
        all_pages = find_confluence_pages(state.project_name, cfg)
        
        discovered_projects = extract_project_groups(all_pages)
        
        if len(discovered_projects) > 1:
            session['discovered_projects'] = discovered_projects
            session['search_type'] = 'confluence'
            session['project_name'] = state.project_name
            session['selected_oem'] = state.selected_oem
            state.show_project_selector = True
            state.discovered_projects = discovered_projects
            state.flash_success = f"{len(discovered_projects)}개의 프로젝트가 발견되었습니다. 선택해주세요."
        else:
            state.confluence_tree = all_pages
            if all_pages:
                state.selected_confluence_page_id = all_pages[0].get("id", "")
                if len(related_projects) > 1:
                    projects_str = ", ".join(related_projects)
                    state.flash_success = f"Confluence 페이지 구조를 불러왔습니다. 관련 프로젝트: {projects_str} (OEM: {state.selected_oem})"
                else:
                    state.flash_success = f"Confluence 페이지 구조를 불러왔습니다. (OEM: {state.selected_oem})"
            else:
                state.flash_error = "Confluence에서 일치하는 페이지를 찾지 못했습니다."
                
    except Exception as exc:
        state.flash_error = str(exc)
        
    return render(state)


@frontend_bp.post("/search/jira")
def search_jira():
    state = build_default_state()
    cfg = load_config()
    
    state.project_name = (request.form.get("project_name") or "").strip()
    state.selected_oem = (request.form.get("oem") or "KGM").strip()
    
    # Restore confluence tree from hidden field
    tree_data = (request.form.get("tree_data") or "").strip()
    if tree_data:
        try:
            import json
            parsed_tree = json.loads(tree_data)
            state.confluence_tree = [parsed_tree] if isinstance(parsed_tree, dict) else parsed_tree
        except Exception:
            pass
    
    detected_oem = detect_oem_from_project_code(state.project_name)
    if detected_oem:
        state.selected_oem = detected_oem
    
    try:
        state.jira_issues = find_jira_issues(state.project_name, cfg)
        state.flash_success = f"Jira 이슈 목록을 불러왔습니다. (OEM: {state.selected_oem})"
    except Exception as exc:
        state.flash_error = str(exc)
    return render(state)


@frontend_bp.post("/jira/create")
def create_jira():
    state = build_default_state()
    cfg = load_config()
    state.project_name = (request.form.get("project_name") or "").strip()
    try:
        payload = jira_create_issue(
            project_key=(request.form.get("jira_project_key") or "").strip(),
            issue_type=(request.form.get("jira_issue_type") or "Task").strip(),
            summary=(request.form.get("jira_summary") or "").strip(),
            description=(request.form.get("jira_description") or "").strip(),
            cfg=cfg,
        )
        state.jira_issues = find_jira_issues(state.project_name or payload.get("key", "").split("-", 1)[0], cfg)
        state.flash_success = f"Jira 이슈 `{payload.get('key', '')}` 생성이 완료되었습니다."
    except Exception as exc:
        state.flash_error = str(exc)
    return render(state)


@frontend_bp.post("/jira/update")
def update_jira():
    state = build_default_state()
    cfg = load_config()
    state.project_name = (request.form.get("project_name") or "").strip()
    try:
        issue_key = (request.form.get("jira_issue_key") or "").strip()
        jira_update_issue(
            issue_key=issue_key,
            summary=(request.form.get("jira_update_summary") or "").strip(),
            description=(request.form.get("jira_update_description") or "").strip(),
            cfg=cfg,
        )
        state.jira_issues = find_jira_issues(state.project_name or issue_key.split("-", 1)[0], cfg)
        state.flash_success = f"Jira 이슈 `{issue_key}` 수정이 완료되었습니다."
    except Exception as exc:
        state.flash_error = str(exc)
    return render(state)


@frontend_bp.post("/confluence/update")
def update_confluence():
    state = build_default_state()
    cfg = load_config()
    state.project_name = (request.form.get("project_name") or "").strip()
    page_id = (request.form.get("confluence_page_id") or "").strip()
    
    if not page_id:
        state.flash_error = "페이지를 선택해주세요."
        return render(state)
    
    try:
        import requests as req_lib
        from backend import auth_headers
        
        # 디버깅: 수신된 데이터 확인
        print(f"=== DEBUG: request.files keys: {list(request.files.keys())}")
        print(f"=== DEBUG: request.form keys: {list(request.form.keys())}")
        print(f"=== DEBUG: content_type: {request.content_type}")
        
        # 1. 파일을 먼저 업로드
        files = request.files.getlist('files')
        valid_files = [f for f in files if f and f.filename]
        print(f"=== DEBUG: files count: {len(files)}, valid: {len(valid_files)}")
        uploaded_filenames = []
        
        for file in valid_files:
            try:
                confluence_upload_attachment(page_id, file, cfg)
                uploaded_filenames.append(file.filename)
                print(f"Uploaded: {file.filename}")
            except Exception as upload_exc:
                print(f"File upload failed for {file.filename}: {upload_exc}")
        
        # 2. 항상 첨부 파일 목록 조회 (신규 업로드 여부와 무관하게)
        #    에디터에 파일 텍스트가 있으면 기존 첨부에서도 URL을 찾아 링크 생성
        file_download_links = {}
        try:
            att_url = f"{cfg.confluence_base_url}/rest/api/content/{page_id}/child/attachment?limit=50"
            att_resp = req_lib.get(att_url, headers=auth_headers(cfg.confluence_pat), timeout=10)
            att_resp.raise_for_status()
            for att in att_resp.json().get('results', []):
                title = att.get('title', '')
                dl_link = att.get('_links', {}).get('download', '')
                if title and dl_link:
                    full_url = f"{cfg.confluence_base_url}{dl_link}"
                    file_download_links[title] = full_url
                    print(f"Attachment URL: {title} → {full_url}")
        except Exception as att_exc:
            print(f"Attachment list failed: {att_exc}")
        
        # 3. 수집된 다운로드 링크와 함께 페이지 업데이트
        confluence_update_page(
            page_id=page_id,
            append_text=(request.form.get("confluence_append_text") or "").strip(),
            title=(request.form.get("confluence_title") or "").strip(),
            cfg=cfg,
            file_download_links=file_download_links if file_download_links else None,
        )
        
        # Only reload tree if project_name is provided
        if state.project_name:
            state.confluence_tree = find_confluence_pages(state.project_name, cfg)
        state.selected_confluence_page_id = page_id
        
        if valid_files:
            state.flash_success = f"Confluence 페이지 수정 및 파일 {len(valid_files)}개 업로드가 완료되었습니다."
        else:
            state.flash_success = "Confluence 페이지 수정이 완료되었습니다."
    except Exception as exc:
        state.flash_error = str(exc)
    return render(state)


@frontend_bp.post("/confluence/upload")
def upload_confluence():
    state = build_default_state()
    cfg = load_config()
    state.project_name = (request.form.get("project_name") or "").strip()
    page_id = (request.form.get("confluence_upload_page_id") or "").strip()
    upload = request.files.get("confluence_file")
    
    if not page_id:
        state.flash_error = "페이지를 선택해주세요."
        return render(state)
    
    try:
        if upload is None or not upload.filename:
            raise ValueError("업로드할 파일을 선택해 주세요.")
        confluence_upload_attachment(page_id, upload, cfg)
        # Only reload tree if project_name is provided
        if state.project_name:
            state.confluence_tree = find_confluence_pages(state.project_name, cfg)
        state.selected_confluence_page_id = page_id
        state.flash_success = "Confluence 첨부 업로드가 완료되었습니다."
    except Exception as exc:
        state.flash_error = str(exc)
    return render(state)


@frontend_bp.post("/training/generate")
def create_training():
    state = build_default_state()
    state.project_name = (request.form.get("project_name") or "").strip()
    try:
        state.training_output = generate_training_engine()
        state.flash_success = "training_engine.md 생성을 완료했습니다."
    except Exception as exc:
        state.flash_error = str(exc)
    return render(state)


@frontend_bp.post("/api/chat")
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        session_id = data.get("session_id", "default")
        
        if not user_message:
            return jsonify({"success": False, "message": "메시지를 입력해주세요."}), 400
        
        cfg = load_config()
        
        if not cfg.openai_api_key:
            return jsonify({
                "success": False,
                "message": "OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요."
            }), 400
        
        if session_id not in chat_sessions:
            chat_sessions[session_id] = CodexChatService(cfg) if _use_codex else ChatService(cfg)
        
        chat_service = chat_sessions[session_id]
        result = chat_service.process_message(user_message)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"오류가 발생했습니다: {str(e)}"
        }), 500


@frontend_bp.post("/api/chat/clear")
def clear_chat():
    try:
        data = request.get_json()
        session_id = data.get("session_id", "default")
        
        if session_id in chat_sessions:
            chat_sessions[session_id].clear_history()
        
        return jsonify({"success": True, "message": "대화 이력이 초기화되었습니다."})
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"오류가 발생했습니다: {str(e)}"
        }), 500


@frontend_bp.get("/api/chat/history")
def get_chat_history():
    try:
        session_id = request.args.get("session_id", "default")
        
        if session_id not in chat_sessions:
            return jsonify({"success": True, "history": []})
        
        history = chat_sessions[session_id].get_history()
        return jsonify({"success": True, "history": history})
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"오류가 발생했습니다: {str(e)}"
        }), 500


# ---------------------------------------------------------------------------
# Document management API
# ---------------------------------------------------------------------------

@frontend_bp.post("/api/documents")
def upload_document():
    """문서 업로드 및 Vector Store 색인"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "message": "파일이 첨부되지 않았습니다."}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"success": False, "message": "파일명이 없습니다."}), 400

        source_type = request.form.get("source_type", "spec")
        title = request.form.get("title", file.filename)
        version = request.form.get("version")
        effective_from = request.form.get("effective_from")
        department = request.form.get("department")

        cfg = load_config()
        from document_store import DocumentStore

        store = DocumentStore(cfg)
        result = store.upload_document(
            file_storage=file,
            source_type=source_type,
            title=title,
            version=version,
            effective_from=effective_from,
            department=department,
        )
        return jsonify({"success": True, **result})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@frontend_bp.get("/api/documents")
def list_documents():
    """업로드된 문서 목록 조회"""
    try:
        source_type = request.args.get("source_type")
        limit = request.args.get("limit", 20, type=int)

        cfg = load_config()
        from document_store import DocumentStore

        store = DocumentStore(cfg)
        docs = store.list_documents(source_type=source_type, limit=limit)
        return jsonify({"success": True, "documents": docs})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@frontend_bp.post("/api/documents/<int:doc_id>/reindex")
def reindex_document(doc_id: int):
    """문서 재색인"""
    try:
        cfg = load_config()
        from document_store import DocumentStore

        store = DocumentStore(cfg)
        result = store.reindex_document(doc_id)
        return jsonify({"success": True, **result})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ---------------------------------------------------------------------------
# Project filtering API
# ---------------------------------------------------------------------------

@frontend_bp.post("/api/filter-projects")
def filter_projects():
    try:
        data = request.get_json()
        project_ids = data.get("project_ids", [])
        
        all_projects = session.get('discovered_projects', [])
        
        filtered = [p for p in all_projects if p.get('id') in project_ids]
        
        session['filtered_projects'] = filtered
        
        return jsonify({"success": True, "projects": filtered})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@frontend_bp.get("/api/oem-projects/<oem>")
def get_oem_projects_api(oem: str):
    try:
        cfg = load_config()
        projects = get_oem_projects(oem, cfg)
        
        return jsonify({"success": True, "projects": projects})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@frontend_bp.post("/api/load-project-tree")
def load_project_tree():
    try:
        data = request.get_json()
        project_id = data.get("project_id", "")
        project_title = data.get("project_title", "")
        
        if not project_id:
            return jsonify({"success": False, "message": "프로젝트 ID가 필요합니다."}), 400
        
        cfg = load_config()
        
        root = {
            "id": project_id,
            "title": project_title,
            "url": f"{cfg.confluence_base_url}/pages/viewpage.action?pageId={project_id}"
        }
        
        tree = build_confluence_tree_from_root(root, cfg)
        tree_dict = confluence_tree_to_dict(tree)
        
        return jsonify({"success": True, "tree": tree_dict})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@frontend_bp.get("/confluence/download/<page_id>/<path:filename>")
def download_confluence_file(page_id: str, filename: str):
    """Confluence 첨부 파일 다운로드 프록시"""
    import requests
    from urllib.parse import quote, unquote
    from backend import auth_headers
    
    cfg = load_config()
    
    try:
        print(f"Requested filename: {filename}")  # 디버깅용
        
        # 먼저 페이지의 첨부 파일 목록을 가져와서 정확한 파일명 찾기
        attachments_url = f"{cfg.confluence_base_url}/rest/api/content/{page_id}/child/attachment"
        attachments_response = requests.get(
            attachments_url,
            headers=auth_headers(cfg.confluence_pat),
            timeout=10
        )
        attachments_response.raise_for_status()
        attachments_data = attachments_response.json()
        
        # 요청된 파일명과 일치하는 첨부 파일 찾기
        target_attachment = None
        for attachment in attachments_data.get('results', []):
            if attachment['title'] == filename:
                target_attachment = attachment
                break
        
        if not target_attachment:
            return f"파일을 찾을 수 없습니다: {filename}", 404
        
        # 첨부 파일의 다운로드 링크 사용
        download_link = target_attachment['_links']['download']
        download_url = f"{cfg.confluence_base_url}{download_link}"
        
        print(f"Downloading from: {download_url}")  # 디버깅용
        
        # Confluence에서 파일 가져오기
        response = requests.get(
            download_url,
            headers=auth_headers(cfg.confluence_pat),
            stream=True,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")  # 디버깅용
        response.raise_for_status()
        
        # 파일명을 UTF-8로 인코딩
        encoded_filename = quote(filename, safe='')
        
        # 파일 다운로드 응답 생성
        return Response(
            response.iter_content(chunk_size=8192),
            content_type=response.headers.get('Content-Type', 'application/octet-stream'),
            headers={
                'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}'
            }
        )
    except Exception as e:
        print(f"Download error: {str(e)}")  # 디버깅용
        import traceback
        traceback.print_exc()
        return f"파일 다운로드 실패: {str(e)}", 500


@frontend_bp.post("/api/add-table-rows/<page_id>")
def add_table_rows(page_id: str):
    """Add rows to Confluence table with file uploads"""
    import requests
    from bs4 import BeautifulSoup
    from backend import auth_headers, confluence_get_page, confluence_upload_attachment
    
    cfg = load_config()
    
    try:
        # Get form data (multipart/form-data for file uploads)
        rows_json = request.form.get('rows')
        if not rows_json:
            return jsonify({"success": False, "message": "행 데이터가 없습니다."}), 400
        
        import json
        rows = json.loads(rows_json)
        
        if not rows:
            return jsonify({"success": False, "message": "추가할 행이 없습니다."}), 400
        
        # Upload files and collect filenames (overwrite if exists)
        uploaded_files = {}
        for i, row_data in enumerate(rows):
            file_key = f'file_{i}'
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    # Upload to Confluence (will overwrite if file exists)
                    result = confluence_upload_attachment(page_id, file, cfg)
                    actual_filename = result.get('title', file.filename)
                    uploaded_files[i] = actual_filename  # Use actual filename from Confluence
                    print(f"Uploaded file: {file.filename} -> Actual: {actual_filename}")
                    
                    # Debug: Compare filenames
                    if file.filename != actual_filename:
                        print(f"[WARNING] Filename changed during upload!")
        
        # Get current page content
        page = confluence_get_page(page_id, cfg)
        current_body = page.get("body", {}).get("storage", {}).get("value", "")
        
        # Parse HTML with html.parser (xml parser has encoding issues)
        soup = BeautifulSoup(current_body, "html.parser")
        
        # Find the table under "1. Project Requirement"
        heading = None
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'strong']):
            if 'Project Requirement' in h.get_text():
                heading = h
                break
        
        if heading:
            # Find the next table after this heading
            table = heading.find_next('table')
        else:
            table = soup.find('table')
        
        if not table:
            return jsonify({"success": False, "message": "테이블을 찾을 수 없습니다."}), 404
        
        # Find an existing file link in the table to use as template
        existing_link_template = None
        for row in table.find_all("tr")[1:]:  # Skip header
            cells = row.find_all("td")
            if len(cells) > 1:
                # Check if second cell (requirement) has a file link
                link = cells[1].find("ac:link")
                if link:
                    existing_link_template = link
                    print(f"Found existing link structure: {str(link)[:200]}")
                    break
        
        if not existing_link_template:
            print("No existing link found, will use manual structure")
        
        # Find tbody or create if not exists
        tbody = table.find("tbody")
        if not tbody:
            tbody = soup.new_tag("tbody")
            table.append(tbody)
        
        # Add new rows to table
        for i, row_data in enumerate(rows):
            tr = soup.new_tag("tr")
            
            # Use uploaded filename if available
            requirement_value = uploaded_files.get(i, row_data.get('requirement', ''))
            
            # Create 7 cells only (exclude delete button column)
            # Confluence table structure: ##, Project Requirement, Phase, Revision, Date, Author, Comment
            cells = [
                row_data.get('number', ''),
                requirement_value,  # Use uploaded filename
                row_data.get('phase', ''),
                row_data.get('revision', ''),
                row_data.get('date', ''),
                row_data.get('author', ''),
                row_data.get('comment', '')
            ]
            
            for j, cell_value in enumerate(cells):
                td = soup.new_tag("td")
                
                # For requirement column with uploaded file, create Confluence attachment link
                if j == 1 and i in uploaded_files:
                    # Use actual filename from Confluence
                    actual_filename = uploaded_files[i]
                    print(f"Creating Confluence link for row {i}: {actual_filename}")
                    
                    if existing_link_template:
                        # Recreate link structure based on existing template
                        # Get the structure from existing link
                        existing_attachment = existing_link_template.find("ri:attachment")
                        existing_link_body = existing_link_template.find("ac:plain-text-link-body")
                        
                        # Create new link with same structure
                        link = soup.new_tag("ac:link")
                        
                        # Copy all attributes from existing link
                        for attr, value in existing_link_template.attrs.items():
                            link[attr] = value
                        
                        # Create attachment tag with same attributes as existing
                        attachment = soup.new_tag("ri:attachment")
                        if existing_attachment:
                            for attr, value in existing_attachment.attrs.items():
                                if attr != 'ri:filename':  # Skip filename, we'll set it new
                                    attachment[attr] = value
                        attachment['ri:filename'] = str(actual_filename)
                        link.append(attachment)
                        
                        # Add link body if existing template has it
                        if existing_link_body:
                            link_body = soup.new_tag("ac:plain-text-link-body")
                            for attr, value in existing_link_body.attrs.items():
                                link_body[attr] = value
                            link_body.string = str(actual_filename)
                            link.append(link_body)
                        
                        print(f"Recreated link structure: {str(link)[:200]}")
                        td.append(link)
                    else:
                        # Fallback: create minimal link structure
                        print("Using fallback minimal link structure")
                        link = soup.new_tag("ac:link")
                        attachment = soup.new_tag("ri:attachment")
                        attachment['ri:filename'] = str(actual_filename)
                        link.append(attachment)
                        td.append(link)
                else:
                    # Handle multiline content
                    if '\n' in str(cell_value):
                        lines = str(cell_value).split('\n')
                        for k, line in enumerate(lines):
                            if k > 0:
                                td.append(soup.new_tag("br"))
                            td.append(line)
                    else:
                        td.string = str(cell_value) if cell_value else ''
                
                tr.append(td)
            
            tbody.append(tr)
        
        # Update page (use decode to avoid cp949 encoding issues on Windows)
        try:
            new_body = soup.decode()
        except:
            # Fallback: encode to bytes then decode as UTF-8
            new_body = soup.encode('utf-8', errors='ignore').decode('utf-8')
        next_version = int(page.get("version", {}).get("number", 1)) + 1
        
        update_payload = {
            "id": page_id,
            "type": "page",
            "title": page.get("title", ""),
            "space": {"key": page.get("space", {}).get("key", "")},
            "version": {"number": next_version},
            "body": {"storage": {"value": new_body, "representation": "storage"}}
        }
        
        url = f"{cfg.confluence_base_url}/rest/api/content/{page_id}"
        headers = auth_headers(cfg.confluence_pat)
        headers["Content-Type"] = "application/json"
        
        resp = requests.put(url, headers=headers, json=update_payload, timeout=30)
        resp.raise_for_status()
        
        return jsonify({
            "success": True,
            "message": f"{len(rows)}개 행이 추가되었습니다.",
            "added_count": len(rows),
            "uploaded_files": len(uploaded_files)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@frontend_bp.get("/api/fetch-rqmt-table/<page_id>")
def fetch_rqmt_table(page_id: str):
    """Fetch and parse table from Confluence RQMT page"""
    import requests
    import os
    from bs4 import BeautifulSoup
    from backend import auth_headers
    
    cfg = load_config()
    DEBUG_RQMT = os.getenv("DEBUG_RQMT", "false").lower() == "true"
    
    try:
        url = f"{cfg.confluence_base_url}/rest/api/content/{page_id}?expand=body.storage"
        headers = auth_headers(cfg.confluence_pat)
        headers["Accept"] = "application/json"
        
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        
        data = resp.json()
        raw_html = data.get("body", {}).get("storage", {}).get("value", "")
        
        if not raw_html:
            return jsonify({"success": False, "message": "페이지 내용이 없습니다."}), 404
        
        # Debug: Save raw HTML
        if DEBUG_RQMT:
            os.makedirs("logs", exist_ok=True)
            with open("logs/rqmt_table_debug.html", "w", encoding="utf-8") as f:
                f.write(raw_html)
            print(f"[DEBUG] Raw HTML saved to logs/rqmt_table_debug.html")
        
        soup = BeautifulSoup(raw_html, "html.parser")
        table = soup.find("table")
        
        if not table:
            return jsonify({"success": False, "message": "테이블을 찾을 수 없습니다."}), 404
        
        def safe_get_text(element, method="default"):
            """Safely extract text from element with encoding error handling"""
            try:
                if method == "link":
                    # Check for Confluence attachment macro
                    attachment = element.find("ri:attachment")
                    if attachment and attachment.get("ri:filename"):
                        return attachment.get("ri:filename")
                    
                    # Check for regular link
                    link = element.find("a")
                    if link:
                        return link.get_text(separator=" ", strip=True)
                elif method == "time":
                    time_tag = element.find("time")
                    if time_tag:
                        # Get datetime attribute first, fallback to text
                        dt = time_tag.get("datetime")
                        if dt:
                            return dt
                        return time_tag.get_text(separator=" ", strip=True)
                
                # Default: use separator for nested elements
                return element.get_text(separator=" ", strip=True)
            except Exception as e:
                if DEBUG_RQMT:
                    print(f"[ERROR] Text extraction failed: {e}")
                # Fallback: try to get any text content
                try:
                    return str(element.string or "").strip()
                except:
                    return ""
        
        # Parse headers
        headers_row = table.find("tr")
        headers = []
        if headers_row:
            for th in headers_row.find_all(["th", "td"]):
                headers.append(safe_get_text(th))
        
        # Parse rows with improved text extraction
        rows = []
        for row_idx, tr in enumerate(table.find_all("tr")[1:]):  # Skip header row
            cells = []
            for cell_idx, td in enumerate(tr.find_all("td")):
                # Debug: Log cell structure
                if DEBUG_RQMT and row_idx < 3:  # Only first 3 rows
                    try:
                        print(f"\n=== Row {row_idx}, Cell {cell_idx} ===")
                        print(f"HTML preview: {str(td)[:200]}...")
                    except:
                        print(f"\n=== Row {row_idx}, Cell {cell_idx} === (HTML print failed)")
                
                # Try multiple extraction methods
                text = safe_get_text(td, "link")
                if not text:
                    text = safe_get_text(td, "time")
                if not text:
                    text = safe_get_text(td)
                
                if DEBUG_RQMT and row_idx < 3:
                    print(f"Extracted text: '{text}'")
                
                cells.append(text if text else "")
            
            if cells:
                rows.append(cells)
        
        if DEBUG_RQMT:
            print(f"\n[DEBUG] Parsed {len(rows)} rows")
            print(f"[DEBUG] Headers: {headers}")
            if rows:
                print(f"[DEBUG] First row: {rows[0]}")
        
        return jsonify({
            "success": True,
            "headers": headers,
            "rows": rows,
            "page_title": data.get("title", "")
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
