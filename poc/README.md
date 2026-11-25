# Fix Agent POC

Design: [../docs/POC_Fix_Agent_Design.md](../docs/POC_Fix_Agent_Design.md)

| Path | What |
|---|---|
| `fix_agent/` | ADK agent (`agent.py`) + tools with guardrails (`tools.py`) |
| `sample_site/` | Template for the sandbox target repo (simple HTML site + tests + `.agent.json`) |
| `Dockerfile`, `docker-compose.yml` | Runs ADK in Linux on port 8000 |
| `workspace/agent-poc-sandbox/` | Local Git repo the agent works on (git-ignored; recreate from `sample_site/`) |

## Planted demo issues (kept here, not in the sandbox, so the agent can't read the answer)
1. **Broken link:** `index.html` links to `abuot.html`. The link test fails.
   Task: *"The About link on the home page is broken. Fix it."*
2. **Email field:** the contact form's email input is `type="text"` and not required. No test covers it.
   Task (later): *"Make the contact form's email field required and only accept valid email addresses."*

## Tool test without Gemini (done 25 Nov 2026)
All 9 tools passed a simulated run in Docker:
- the agent can't edit before creating a branch, can't touch `tests/` or anything outside the repo, and edits that match more than once are refused;
- the fix took the tests from failed to passed;
- the commit happened locally (no GitHub token yet).

## Run (after billing + Vertex AI API)
```powershell
gcloud auth application-default login
```
```powershell
cd poc; docker compose up --build
```
- Chat UI: http://localhost:8000 → pick `fix_agent`.
- API: create a session, then `POST /run` with the task (exact calls to be added after the first live run).

## Reset the sandbox for a fresh demo
```powershell
Remove-Item -Recurse -Force workspace\agent-poc-sandbox; Copy-Item -Recurse sample_site workspace\agent-poc-sandbox; cd workspace\agent-poc-sandbox; git init -b main; git add -A; git commit -m "Sample site"
```
