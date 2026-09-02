# TrueForge Email Skill + MCP POC

Email-only POC that bypasses LangGraph orchestration while reusing the existing Resulticks catalogue and Email backend integrations.

## Architecture

```text
TrueForge Chat / Agent Loop
        ↓
Installed modular SKILL.md packs
        ↓
Remote MCP: http://localhost:8833/mcp/
        ↓
trueforge_skill_mcp_email capability layer
        ↓
Existing Resulticks catalogue + Email backend integrations
        ↓
Resulticks APIs
```

The existing `/workflow/process` LangGraph path remains unchanged for side-by-side comparison. The POC does not call `process_agentic_request()` or `run_agentic_workflow()`.

## Setup

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Copy `request_context.example.json` to `request_context.local.json` and fill it using a current working `/workflow/process` request. Keep current `t1`, `b1`, auth/reqs, client/user/department data and `userManifestModel.serverInfo` for `cust`, `camp`, `offr`, `aud`.

3. Start:

```powershell
.\scripts\start_trueforge_email_skill_mcp_poc.ps1
```

4. Check:

```text
http://localhost:8833/health
```

Expected important values:

```text
mcp_available = true
request_context.ok = true
langgraph_orchestration = false
```

5. Add the remote MCP server to TrueForge:

```text
http://localhost:8833/mcp/
```

6. Put the six folders under `trueforge_skill_mcp_email/skills/` into a Git repository accessible to TrueForge and attach them to the Email POC agent. Use `TRUEFORGE_AGENT_INSTRUCTIONS.md` as the short base instruction.

## Validation lifecycle

```text
Create Email
  ↓
Validate Product (+ optional Sub-product)
  ↓
Validate Communication Type
  ↓
Validate Audience
  ↓
Communication Details review
  ↓
Confirm
  ↓
Generate / Upload / Existing EDM
  ↓
Verified saved draft
  ↓
View / Edit / Revert / Test Preview
  ↓
RFA with approver + intended schedule time
  ↓
Live approval/status
```

Critical lifecycle rules remain deterministic at the MCP/tool boundary. In particular, this POC exposes no direct Email scheduling backend operation; schedule requests enter the mandatory RFA path.
