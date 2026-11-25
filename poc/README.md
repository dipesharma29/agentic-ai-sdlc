# Fix Agent POC

Design: [../docs/POC_Fix_Agent_Design.md](../docs/POC_Fix_Agent_Design.md)

| Path | What |
|---|---|
| `fix_agent/` | ADK agent (`agent.py`) + tools with guardrails (`tools.py`) |
| `sample_site/` | Template for the sandbox target repo (simple HTML site + tests + `.agent.json`) |
| `Dockerfile`, `docker-compose.yml` | Runs ADK in Linux on port 8000 |
| `call_agent.py` | Sends a task to the agent over ADK's REST API; approves or rejects the commit/PR |
| `workspace/agentic-ai-sdlc/` | Separate clone of this repo that the agent works in (git-ignored) |

## Target repo
For now the agent works on **this repo** and opens PRs here. The root `.agent.json` limits it:
it can edit only `poc/sample_site/` (not its tests), and runs only the sample site's tests.
Later, point `TARGET_REPO`/`GITHUB_REPO` at the real project and give that repo its own `.agent.json`.

## Planted demo issues in `sample_site/`
The agent can read the whole repo, including this file. That's acceptable for the demo since each task names the problem anyway.
1. **Broken link:** `index.html` links to `abuot.html`. The link test fails.
   Task: *"The About link on the home page is broken. Fix it."*
2. **Email field:** the contact form's email input is `type="text"` and not required. No test covers it.
   Task (later): *"Make the contact form's email field required and only accept valid email addresses."*

## Tool test without Gemini (done 25 Nov 2026)
All 9 tools passed a simulated run in Docker:
- the agent can't edit before creating a branch, can't touch `tests/` or anything outside the repo, and edits that match more than once are refused;
- the fix took the tests from failed to passed;
- the commit happened locally (no GitHub token yet).

## Run
1. Copy `fix_agent/.env.example` to `fix_agent/.env` and add your own `GITHUB_TOKEN`.
2. Google access: put your key for service account `fix-agent@ai-sdlc-515307.iam.gserviceaccount.com`
   (role: Vertex AI User) at `poc/secrets/fix-agent-key.json`. The folder is git-ignored. Get the key
   from the project owner; never commit or paste it anywhere.
3. Clone the target repo for the agent and start it (from `poc/`):
```powershell
git clone https://github.com/dipesharma29/agentic-ai-sdlc.git workspace\agentic-ai-sdlc
```
```powershell
docker compose up --build
```
- Chat UI: http://localhost:8000 → pick `fix_agent`.
- API (from `poc/`):
```powershell
python call_agent.py "The About link on the home page is broken. Fix it."
```
```powershell
python call_agent.py --approve <session_id>
```
Under the hood: `POST /apps/fix_agent/users/<user>/sessions/<id>` creates a session, `POST /run`
sends the task, and approval is a `functionResponse` to `adk_request_confirmation` with `{"confirmed": true}`.

Restart the container after editing `.env` (`docker compose up -d --force-recreate`).
