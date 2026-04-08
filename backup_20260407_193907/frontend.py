from __future__ import annotations

from flask import Blueprint, render_template, request

from backend import (
    SearchState,
    confluence_update_page,
    confluence_upload_attachment,
    export_mcp_config,
    find_confluence_pages,
    find_jira_issues,
    generate_training_engine,
    get_recent_activity,
    jira_create_issue,
    jira_update_issue,
    load_config,
)

frontend_bp = Blueprint("frontend", __name__)


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
    return render(build_default_state())


@frontend_bp.post("/search/confluence")
def search_confluence():
    state = build_default_state()
    cfg = load_config()
    state.project_name = (request.form.get("project_name") or "").strip()
    try:
        state.confluence_tree = find_confluence_pages(state.project_name, cfg)
        if state.confluence_tree:
            state.selected_confluence_page_id = state.confluence_tree[0].get("id", "")
            state.flash_success = "Confluence 페이지 구조를 불러왔습니다."
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
    try:
        state.jira_issues = find_jira_issues(state.project_name, cfg)
        state.flash_success = "Jira 이슈 목록을 불러왔습니다."
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
