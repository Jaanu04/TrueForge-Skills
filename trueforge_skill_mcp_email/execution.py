from __future__ import annotations

from typing import Any, Dict

from agentic_workflow.channels.email import tools as email_tools
from agentic_workflow.channels.email.template_service import (
    EmailTemplateAPIError,
    compact_email_template_options,
    fetch_email_templates,
    resolve_trusted_template_selection,
    verified_template_from_filtered_items,
)
from agentic_workflow.mcp_tools.business_utils import ensure_business_session

from .policies import guard_rfa, guard_setup_complete, guard_test_preview, valid_email
from .state import build_state, persist_state, session_summary, set_known_fields

_EDITABLE_SETUP_FIELDS = {
    "campaign_name", "start_date", "end_date", "goal", "goal_value",
    "sender_name", "sender_email", "subject", "preview_text",
    "test_recipient", "approver_email", "schedule_datetime",
}


def _result(state: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
    persist_state(state)
    sid = str((state.get("context") or {}).get("spaceid") or "")
    result = dict(raw or {})
    result.setdefault("ok", not str(result.get("workflow_status") or "").endswith("ERROR"))
    result["spaceid"] = sid
    result["state"] = session_summary(sid)
    return result


def update_setup(spaceid: str, values: Dict[str, Any]) -> Dict[str, Any]:
    state = build_state(spaceid, prompt="Update Email setup", intent_type="edit")
    requested = dict(values or {})
    disallowed = sorted(set(requested) - _EDITABLE_SETUP_FIELDS)
    if disallowed:
        return _result(state, {"ok": False, "workflow_status": "EMAIL_SETUP_FIELD_NOT_DIRECTLY_EDITABLE", "message": "Some fields require their dedicated validation tool before they can be stored.", "rejected_fields": disallowed, "allowed_fields": sorted(_EDITABLE_SETUP_FIELDS)})
    normalized: Dict[str, Any] = {}
    for key, value in requested.items():
        if value in (None, "", [], {}):
            continue
        text = str(value).strip() if isinstance(value, str) else value
        if key in {"sender_email", "test_recipient", "approver_email"} and text and not valid_email(str(text)):
            return _result(state, {"ok": False, "workflow_status": "EMAIL_ADDRESS_INVALID", "message": f"{key} must contain a valid email address.", "field": key})
        normalized[key] = text
    changed = set_known_fields(state, normalized)
    return _result(state, {"ok": True, "workflow_status": "EMAIL_SETUP_UPDATED", "message": "Email setup values updated.", "updated_fields": changed})


def review_setup(spaceid: str) -> Dict[str, Any]:
    state = build_state(spaceid, prompt="Review Email Communication Details", intent_type="create")
    ok, missing = guard_setup_complete(state.get("known_fields") or {})
    if not ok:
        return _result(state, {"ok": False, "workflow_status": "EMAIL_SETUP_FIELDS_REQUIRED", "message": "Validate the required Email setup values before opening Communication Details.", "missing_fields": missing})
    return _result(state, email_tools.email_create_draft({}, state))


def confirm_setup(spaceid: str) -> Dict[str, Any]:
    state = build_state(spaceid, prompt="Confirm", intent_type="create")
    return _result(state, email_tools.email_create_draft({}, state))


def generate_edm(spaceid: str) -> Dict[str, Any]:
    state = build_state(spaceid, prompt="Generate New EDM", intent_type="create")
    state.setdefault("normalized_intent", {}).setdefault("extracted_fields", {})["edm_source_choice"] = "generate"
    return _result(state, email_tools.email_create_draft({}, state))


def use_uploaded_edm(spaceid: str, edm_html: str) -> Dict[str, Any]:
    html = str(edm_html or "").strip()
    if not html:
        return {"ok": False, "spaceid": spaceid, "workflow_status": "EMAIL_EDM_HTML_REQUIRED", "message": "Provide extracted EDM HTML before selecting uploaded creative."}
    state = build_state(spaceid, prompt="Use Uploaded EDM", intent_type="create")
    fields = state.setdefault("normalized_intent", {}).setdefault("extracted_fields", {})
    fields["edm_source_choice"] = "uploaded"
    fields["edm_html"] = html
    state.setdefault("context", {})["edmHTML"] = html
    state["context"]["uploaded_edm"] = {"available": True, "attachment_present": True, "html": html, "source": "skill_mcp_tool"}
    set_known_fields(state, {"edm_html": html, "edm_html_available": True, "edm_source_choice": "uploaded"})
    return _result(state, email_tools.email_create_draft({"edm_html": html}, state))


def list_existing_edms(spaceid: str, query: str = "") -> Dict[str, Any]:
    state = build_state(spaceid, prompt="Show Available EDMs", intent_type="create")
    if not session_summary(spaceid).get("setup_confirmed"):
        return _result(state, {"ok": False, "workflow_status": "EMAIL_SETUP_CONFIRMATION_REQUIRED", "message": "Confirm the Communication Details before choosing an Email creative source."})
    state.setdefault("normalized_intent", {}).setdefault("extracted_fields", {})["edm_source_choice"] = "existing_template"
    search = str(query or "").strip()
    try:
        items = fetch_email_templates(state, template_name=search, is_filter=bool(search), page_no=1)
        compact = compact_email_template_options(items)
        agentic = state.setdefault("session", {}).setdefault("agentic", {})
        agentic["skill_mcp_email_template_options"] = compact
        agentic["skill_mcp_email_template_query"] = search
        persist_state(state)
        return {"ok": True, "spaceid": spaceid, "workflow_status": "EMAIL_EDM_TEMPLATES_AVAILABLE", "items": compact, "total": len(compact), "message": "Select an existing Email EDM by number, exact template name, or template ID." if compact else "No Email EDM templates matched the current lookup.", "state": session_summary(spaceid)}
    except EmailTemplateAPIError as exc:
        return _result(state, {"ok": False, "workflow_status": "EMAIL_EDM_TEMPLATE_LOOKUP_FAILED", "message": str(exc)})


def select_existing_edm(spaceid: str, selection: str) -> Dict[str, Any]:
    text = str(selection or "").strip()
    if not text:
        return {"ok": False, "spaceid": spaceid, "workflow_status": "EMAIL_EDM_TEMPLATE_SELECTION_REQUIRED", "message": "Select an Email EDM by number, name, or template ID."}
    state = build_state(spaceid, prompt=f"Use existing EDM {text}", intent_type="create")
    fields = state.setdefault("normalized_intent", {}).setdefault("extracted_fields", {})
    fields["edm_source_choice"] = "existing_template"
    fields["edm_template_selection"] = text
    agentic = state.setdefault("session", {}).setdefault("agentic", {})
    options = agentic.get("skill_mcp_email_template_options") if isinstance(agentic.get("skill_mcp_email_template_options"), list) else []
    selected_option = resolve_trusted_template_selection(text, options)
    try:
        if selected_option:
            filtered = fetch_email_templates(state, template_name=str(selected_option.get("templateName") or ""), is_filter=True, page_no=1)
            verified = verified_template_from_filtered_items(filtered, template_id=selected_option.get("templateID"))
        elif not text.isdigit():
            filtered = fetch_email_templates(state, template_name=text, is_filter=True, page_no=1)
            verified = verified_template_from_filtered_items(filtered, template_name=text)
            if not verified and filtered:
                return _result(state, {"ok": False, "workflow_status": "EMAIL_EDM_TEMPLATE_AMBIGUOUS", "message": "That template selection is ambiguous. Choose one of these API-backed options.", "items": compact_email_template_options(filtered)})
        else:
            verified = None
    except EmailTemplateAPIError as exc:
        return _result(state, {"ok": False, "workflow_status": "EMAIL_EDM_TEMPLATE_LOOKUP_FAILED", "message": str(exc)})
    if not verified:
        return _result(state, {"ok": False, "workflow_status": "EMAIL_EDM_TEMPLATE_NOT_VERIFIED", "message": "I could not verify that selection against the current Resulticks Email EDM catalogue. List the templates again and choose one of them.", "items": options})
    email_tools._persist_existing_email_template(state, verified)  # type: ignore[attr-defined]
    raw = email_tools.email_create_draft({}, state)
    result = _result(state, raw)
    result.setdefault("selected_template", {"templateID": verified.get("templateID"), "templateName": verified.get("templateName")})
    return result


def preview(spaceid: str) -> Dict[str, Any]:
    state = build_state(spaceid, prompt="View Email preview", intent_type="state_question")
    return _result(state, email_tools.email_preview({}, state))


def edit(spaceid: str, instruction: str) -> Dict[str, Any]:
    text = str(instruction or "").strip()
    if not text:
        return {"ok": False, "spaceid": spaceid, "workflow_status": "EMAIL_EDIT_INSTRUCTION_REQUIRED", "message": "Provide the Email change you want to make."}
    state = build_state(spaceid, prompt=text, intent_type="edit")
    state["creative_edit_request"] = text
    state.setdefault("normalized_intent", {})["requested_action"] = "edit_edm"
    return _result(state, email_tools.email_edit_draft({"feedback": text}, state))


def revert(spaceid: str, instruction: str = "revert to previous EDM") -> Dict[str, Any]:
    text = str(instruction or "revert to previous EDM").strip()
    state = build_state(spaceid, prompt=text, intent_type="edit")
    return _result(state, email_tools.email_revert_draft({"feedback": text}, state))


def test_preview(spaceid: str, recipient: str) -> Dict[str, Any]:
    recipient = str(recipient or "").strip()
    if not valid_email(recipient):
        return {"ok": False, "spaceid": spaceid, "workflow_status": "EMAIL_TEST_RECIPIENT_INVALID", "message": "Provide a valid Test Preview email address."}
    state = build_state(spaceid, prompt=f"Send Test Preview to {recipient}", intent_type="test_send")
    set_known_fields(state, {"test_recipient": recipient})
    summary = session_summary(spaceid)
    allowed, reason = guard_test_preview(state.get("known_fields") or {}, bool(summary.get("draft_created")))
    if not allowed:
        return _result(state, {"ok": False, "workflow_status": "EMAIL_TEST_PREVIEW_BLOCKED", "message": reason})
    return _result(state, email_tools.email_test_send({"test_recipient": recipient}, state))


def request_approval(spaceid: str, approver_email: str, schedule_datetime: str) -> Dict[str, Any]:
    approver = str(approver_email or "").strip()
    schedule = str(schedule_datetime or "").strip()
    if not valid_email(approver):
        return {"ok": False, "spaceid": spaceid, "workflow_status": "EMAIL_APPROVER_INVALID", "message": "Provide a valid approver email address."}
    if not schedule:
        return {"ok": False, "spaceid": spaceid, "workflow_status": "EMAIL_SCHEDULE_DATETIME_REQUIRED", "message": "Provide the intended schedule date and time for the approval request."}
    state = build_state(spaceid, prompt=f"Send RFA to {approver} for {schedule}", intent_type="approve")
    state["normalized_intent"]["lifecycle_actions"] = ["rfa", "schedule"]
    set_known_fields(state, {"approver_email": approver, "schedule_datetime": schedule})
    summary = session_summary(spaceid)
    allowed, reason = guard_rfa(state.get("known_fields") or {}, bool(summary.get("draft_created")))
    if not allowed:
        return _result(state, {"ok": False, "workflow_status": "EMAIL_RFA_BLOCKED", "message": reason})
    ensure_business_session(state, "EMAIL")
    return _result(state, email_tools.email_approve({"approver_email": approver, "schedule_datetime": schedule}, state))


def schedule_request(spaceid: str, schedule_datetime: str = "", approver_email: str = "") -> Dict[str, Any]:
    state = build_state(spaceid, prompt=f"Schedule this Email {schedule_datetime}".strip(), intent_type="schedule")
    state["normalized_intent"]["lifecycle_actions"] = ["rfa", "schedule"]
    values: Dict[str, Any] = {}
    if schedule_datetime:
        values["schedule_datetime"] = str(schedule_datetime).strip()
    if approver_email:
        if not valid_email(approver_email):
            return {"ok": False, "spaceid": spaceid, "workflow_status": "EMAIL_APPROVER_INVALID", "message": "Provide a valid approver email address."}
        values["approver_email"] = str(approver_email).strip()
    if values:
        set_known_fields(state, values)
    return _result(state, email_tools.email_schedule(values, state))


def status(spaceid: str) -> Dict[str, Any]:
    state = build_state(spaceid, prompt="Check Email status", intent_type="state_question")
    return _result(state, email_tools.email_get_draft_status({}, state))
