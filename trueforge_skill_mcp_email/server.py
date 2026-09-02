"""TrueForge-facing Streamable HTTP MCP server for the Email Skill+MCP POC.

This POC intentionally does not invoke ``process_agentic_request`` or any
LangGraph graph runner. TrueForge owns the conversational agent loop and loads
SKILL.md instructions; this MCP server exposes deterministic capabilities that
reuse the existing Resulticks catalogue and Email backend integrations.
"""
from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator
from typing import Any, Callable, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import catalogue, execution, settings
from .context import validate_request_context
from .state import build_state, new_spaceid, normalize_spaceid, persist_state, session_summary

MCP_IMPORT_ERROR = ""
try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings
except ImportError as exc:  # pragma: no cover
    FastMCP = None  # type: ignore[assignment]
    TransportSecuritySettings = None  # type: ignore[assignment]
    MCP_IMPORT_ERROR = str(exc)


def _error(spaceid: str, exc: Exception) -> Dict[str, Any]:
    return {"ok": False, "spaceid": str(spaceid or ""), "workflow_status": "EMAIL_SKILL_MCP_TOOL_ERROR", "message": str(exc), "instruction": "Do not invent a successful result. Use the returned error and ask only for actionable missing information."}


def _safe(spaceid: str, fn: Callable[..., Dict[str, Any]], *args: Any, **kwargs: Any) -> Dict[str, Any]:
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        return _error(spaceid, exc)


mcp = None
mcp_app = None
if FastMCP is not None:
    transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=settings.mcp_allowed_hosts(), allowed_origins=settings.mcp_allowed_origins())
    mcp = FastMCP(
        "Resulticks Email - Skill + MCP POC",
        instructions=(
            "Email-only Resulticks capability server for a TrueForge Skill+MCP POC. "
            "TrueForge and its installed SKILL.md packs own conversation/orchestration. "
            "Reuse one stable spaceid for the whole Email lifecycle. Treat every MCP "
            "response as authoritative. Never invent catalogue IDs or bypass approval. "
            "There is intentionally no direct Email scheduling tool: schedule requests "
            "must enter the RFA/approval lifecycle."
        ),
        host=settings.host(), port=settings.port(), stateless_http=True, json_response=True,
        streamable_http_path="/", transport_security=transport_security,
    )

    @mcp.tool()
    async def email_start_session(spaceid: str = "") -> Dict[str, Any]:
        """Create or initialize one Email POC session and return its current state."""
        sid = normalize_spaceid(spaceid) if str(spaceid or "").strip() else new_spaceid()
        context_check = validate_request_context()
        if not context_check.get("ok"):
            return {"ok": False, "spaceid": sid, "workflow_status": "EMAIL_REQUEST_CONTEXT_NOT_READY", "message": context_check.get("message"), "missing": context_check.get("missing") or []}
        state = _safe(sid, build_state, sid, prompt="Start Email Skill MCP session", intent_type="create")
        if not isinstance(state, dict) or state.get("workflow_status") == "EMAIL_SKILL_MCP_TOOL_ERROR":
            return state
        persist_state(state)
        return {"ok": True, "spaceid": sid, "workflow_status": "EMAIL_SKILL_MCP_READY", "message": "Email Skill+MCP session is ready. Reuse this spaceid for every next tool call.", "state": session_summary(sid)}

    @mcp.tool()
    async def email_get_state(spaceid: str) -> Dict[str, Any]:
        """Return the current trusted Email workflow state for one session."""
        return _safe(spaceid, lambda: {"ok": True, "spaceid": spaceid, "state": session_summary(spaceid)})

    @mcp.tool()
    async def email_catalogue_health(spaceid: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Check whether Product, Communication Type and Audience catalogues are reachable."""
        def run() -> Dict[str, Any]:
            state = build_state(spaceid, prompt="Check Email catalogue", intent_type="state_question")
            result = catalogue.catalogue_health(state, force=force_refresh)
            result.update({"spaceid": spaceid, "workflow_status": "EMAIL_CATALOGUE_READY" if result.get("ok") else "EMAIL_CATALOGUE_INCOMPLETE"})
            return result
        return _safe(spaceid, run)

    @mcp.tool()
    async def email_list_products(spaceid: str, query: str = "", limit: int = 20) -> Dict[str, Any]:
        """List API-backed Resulticks products."""
        def run() -> Dict[str, Any]:
            state = build_state(spaceid, prompt=f"List products {query}".strip(), intent_type="state_question")
            result = catalogue.list_products(state, query=query, limit=limit)
            result.update({"spaceid": spaceid, "workflow_status": "EMAIL_PRODUCTS_AVAILABLE"})
            return result
        return _safe(spaceid, run)

    @mcp.tool()
    async def email_validate_product(spaceid: str, product: str, sub_product: str = "") -> Dict[str, Any]:
        """Validate Product and optional Sub-product against the live Resulticks catalogue."""
        def run() -> Dict[str, Any]:
            state = build_state(spaceid, prompt=f"Product {product} {sub_product}".strip(), intent_type="create")
            result = catalogue.validate_product(state, product, sub_product=sub_product)
            result.update({"spaceid": spaceid, "workflow_status": "EMAIL_PRODUCT_VALIDATED" if result.get("ok") else "EMAIL_PRODUCT_NOT_VALIDATED", "state": session_summary(spaceid)})
            return result
        return _safe(spaceid, run)

    @mcp.tool()
    async def email_list_sub_products(spaceid: str, product: str = "", limit: int = 20) -> Dict[str, Any]:
        """List sub-products for the validated or explicitly supplied Product."""
        def run() -> Dict[str, Any]:
            state = build_state(spaceid, prompt=f"List sub products {product}".strip(), intent_type="state_question")
            result = catalogue.list_sub_products(state, product=product, limit=limit)
            result.update({"spaceid": spaceid, "workflow_status": "EMAIL_SUB_PRODUCTS_AVAILABLE"})
            return result
        return _safe(spaceid, run)

    @mcp.tool()
    async def email_list_communication_types(spaceid: str, query: str = "", limit: int = 20) -> Dict[str, Any]:
        """List API-backed Communication Types."""
        def run() -> Dict[str, Any]:
            state = build_state(spaceid, prompt=f"List communication types {query}".strip(), intent_type="state_question")
            result = catalogue.list_communication_types(state, query=query, limit=limit)
            result.update({"spaceid": spaceid, "workflow_status": "EMAIL_COMMUNICATION_TYPES_AVAILABLE"})
            return result
        return _safe(spaceid, run)

    @mcp.tool()
    async def email_validate_communication_type(spaceid: str, communication_type: str) -> Dict[str, Any]:
        """Validate a Communication Type against the live Resulticks catalogue."""
        def run() -> Dict[str, Any]:
            state = build_state(spaceid, prompt=f"Communication type {communication_type}", intent_type="create")
            result = catalogue.validate_communication_type(state, communication_type)
            result.update({"spaceid": spaceid, "workflow_status": "EMAIL_COMMUNICATION_TYPE_VALIDATED" if result.get("ok") else "EMAIL_COMMUNICATION_TYPE_NOT_VALIDATED", "state": session_summary(spaceid)})
            return result
        return _safe(spaceid, run)

    @mcp.tool()
    async def email_list_audiences(spaceid: str, query: str = "", limit: int = 20) -> Dict[str, Any]:
        """Search/list trusted Resulticks audiences."""
        def run() -> Dict[str, Any]:
            state = build_state(spaceid, prompt=f"List audiences {query}".strip(), intent_type="state_question")
            result = catalogue.list_audiences(state, query=query, limit=limit)
            result.update({"spaceid": spaceid, "workflow_status": "EMAIL_AUDIENCES_AVAILABLE"})
            return result
        return _safe(spaceid, run)

    @mcp.tool()
    async def email_validate_audience(spaceid: str, audience: str) -> Dict[str, Any]:
        """Validate an audience/list against the Resulticks audience service."""
        def run() -> Dict[str, Any]:
            state = build_state(spaceid, prompt=f"Audience {audience}", intent_type="create")
            result = catalogue.validate_audience(state, audience)
            result.update({"spaceid": spaceid, "workflow_status": "EMAIL_AUDIENCE_VALIDATED" if result.get("ok") else "EMAIL_AUDIENCE_NOT_VALIDATED", "state": session_summary(spaceid)})
            return result
        return _safe(spaceid, run)

    @mcp.tool()
    async def email_update_setup(spaceid: str, campaign_name: str = "", start_date: str = "", end_date: str = "", goal: str = "", goal_value: str = "", sender_name: str = "", sender_email: str = "", subject: str = "", preview_text: str = "") -> Dict[str, Any]:
        """Update safe non-catalogue Email setup fields."""
        values = {"campaign_name": campaign_name, "start_date": start_date, "end_date": end_date, "goal": goal, "goal_value": goal_value, "sender_name": sender_name, "sender_email": sender_email, "subject": subject, "preview_text": preview_text}
        return _safe(spaceid, execution.update_setup, spaceid, values)

    @mcp.tool()
    async def email_review_setup(spaceid: str) -> Dict[str, Any]:
        """Open Communication Details after required catalogue values are validated."""
        return _safe(spaceid, execution.review_setup, spaceid)

    @mcp.tool()
    async def email_confirm_setup(spaceid: str) -> Dict[str, Any]:
        """Confirm Communication Details and move to creative-source selection."""
        return _safe(spaceid, execution.confirm_setup, spaceid)

    @mcp.tool()
    async def email_generate_edm(spaceid: str) -> Dict[str, Any]:
        """Generate and save a new Email EDM."""
        return _safe(spaceid, execution.generate_edm, spaceid)

    @mcp.tool()
    async def email_use_uploaded_edm(spaceid: str, edm_html: str) -> Dict[str, Any]:
        """Use extracted uploaded EDM HTML and save the draft."""
        return _safe(spaceid, execution.use_uploaded_edm, spaceid, edm_html)

    @mcp.tool()
    async def email_list_existing_edms(spaceid: str, query: str = "") -> Dict[str, Any]:
        """Browse/search API-backed existing Email EDM templates."""
        return _safe(spaceid, execution.list_existing_edms, spaceid, query)

    @mcp.tool()
    async def email_select_existing_edm(spaceid: str, selection: str) -> Dict[str, Any]:
        """Verify and save a selected existing EDM."""
        return _safe(spaceid, execution.select_existing_edm, spaceid, selection)

    @mcp.tool()
    async def email_preview(spaceid: str) -> Dict[str, Any]:
        """Read the current saved Email creative; never sends."""
        return _safe(spaceid, execution.preview, spaceid)

    @mcp.tool()
    async def email_edit(spaceid: str, instruction: str) -> Dict[str, Any]:
        """Apply user-requested changes to Email details or creative."""
        return _safe(spaceid, execution.edit, spaceid, instruction)

    @mcp.tool()
    async def email_revert(spaceid: str, instruction: str = "revert to previous EDM") -> Dict[str, Any]:
        """Revert Email creative to a persisted version."""
        return _safe(spaceid, execution.revert, spaceid, instruction)

    @mcp.tool()
    async def email_send_test_preview(spaceid: str, recipient: str) -> Dict[str, Any]:
        """Send Test Preview to a validated recipient; saved draft mandatory."""
        return _safe(spaceid, execution.test_preview, spaceid, recipient)

    @mcp.tool()
    async def email_request_approval(spaceid: str, approver_email: str, schedule_datetime: str) -> Dict[str, Any]:
        """Submit saved Email for RFA with approver and intended schedule datetime."""
        return _safe(spaceid, execution.request_approval, spaceid, approver_email, schedule_datetime)

    @mcp.tool()
    async def email_schedule_request(spaceid: str, schedule_datetime: str = "", approver_email: str = "") -> Dict[str, Any]:
        """Handle schedule request through mandatory RFA/approval; never direct schedule."""
        return _safe(spaceid, execution.schedule_request, spaceid, schedule_datetime, approver_email)

    @mcp.tool()
    async def email_get_status(spaceid: str) -> Dict[str, Any]:
        """Return current Email draft/lifecycle status."""
        return _safe(spaceid, execution.status, spaceid)

    mcp_app = mcp.streamable_http_app()


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if mcp is None:
        yield
        return
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="Resulticks Email Skill + MCP POC", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8790", "http://127.0.0.1:8790"], allow_origin_regex=r"^https?://(?:localhost|127\.0\.0\.1)(?::\d+)?$", allow_credentials=False, allow_methods=["GET", "POST", "DELETE", "OPTIONS"], allow_headers=["*"], expose_headers=["Mcp-Session-Id"])


@app.get("/")
async def root(request: Request) -> Dict[str, Any]:
    base = str(request.base_url).rstrip("/")
    return {"name": "Resulticks Email Skill + MCP POC", "mode": "trueforge_skills_plus_mcp", "langgraph_orchestration": False, "health": f"{base}/health", "mcp": f"{base}/mcp/" if mcp is not None else None}


@app.get("/health")
async def health(request: Request) -> Dict[str, Any]:
    base = str(request.base_url).rstrip("/")
    context_check = validate_request_context()
    return {"status": "ok" if mcp is not None and context_check.get("ok") else "needs_configuration", "poc": "trueforge-email-skill-mcp", "email_only": True, "langgraph_orchestration": False, "mcp_available": mcp is not None, "mcp_url": f"{base}/mcp/" if mcp is not None else None, "mcp_error": None if mcp is not None else f"Install mcp>=1.27,<2. {MCP_IMPORT_ERROR}".strip(), "request_context": context_check, "skills_directory": str(settings.PROJECT_ROOT / "trueforge_skill_mcp_email" / "skills"), "trueforge_local_default": "http://localhost:8790"}


@app.get("/api/state/{spaceid}")
async def state_view(spaceid: str) -> Dict[str, Any]:
    return session_summary(spaceid)


if mcp_app is not None:
    app.mount("/mcp", mcp_app)


def main() -> None:
    if not settings.enabled():
        raise SystemExit("trueforge_skill_mcp_email_poc.enabled is false")
    if mcp is None:
        detail = f" ({MCP_IMPORT_ERROR})" if MCP_IMPORT_ERROR else ""
        raise SystemExit("Email Skill+MCP POC requires MCP Python SDK v1 FastMCP. Run pip install -r requirements.txt (mcp>=1.27,<2)." + detail)
    uvicorn.run("trueforge_skill_mcp_email.server:app", host=settings.host(), port=settings.port(), reload=False)


if __name__ == "__main__":
    main()
