from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request, session

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
    get_recent_activity,
    jira_create_issue,
    jira_update_issue,
    load_config,
)
from chat_service import ChatService

frontend_bp = Blueprint("frontend", __name__)

chat_sessions: dict[str, ChatService] = {}


def build_default_state() -> SearchState:
    return SearchState()


def render(state: SearchState):
    cfg = load_config()
    return render_template(
        "index.html",
        state=state,
        recent_activity=get_recent_activity(),
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
    try:
        confluence_update_page(
            page_id=page_id,
            append_text=(request.form.get("confluence_append_text") or "").strip(),
            title=(request.form.get("confluence_title") or "").strip(),
            cfg=cfg,
        )
        state.confluence_tree = find_confluence_pages(state.project_name, cfg)
        state.selected_confluence_page_id = page_id
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
    try:
        if upload is None or not upload.filename:
            raise ValueError("업로드할 파일을 선택해 주세요.")
        confluence_upload_attachment(page_id, upload, cfg)
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
            chat_sessions[session_id] = ChatService(cfg)
        
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
