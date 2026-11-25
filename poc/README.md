# Fix Agent

One agent takes a plain-language task, finds the problem in a target repository,
changes the code, runs that repository's own tests, and opens a pull request for a
human to review. It cannot merge.

Design reasoning: [../docs/POC_Fix_Agent_Design.md](../docs/POC_Fix_Agent_Design.md).
Current status: [../docs/STATE.md](../docs/STATE.md).

| Path | What |
|---|---|
| `fix_agent/` | The agent (`agent.py`) and its tools, with the guardrails in `tools.py` |
| `tests/` | Guardrail tests: each one attempts a forbidden action and asserts the refusal |
| `sample_site/` | The practice target: a small HTML site with its own tests and `.agent.json` |
| `call_agent.py` | Sends a task over ADK's REST API, and approves or rejects the pull request |
| `notebooks/` | The same demonstration in Google Colab, with no local install |
| `Dockerfile`, `docker-compose.yml` | Runs ADK on Linux, serving port 8000 |
| `workspace/agentic-ai-sdlc/` | The separate clone the agent works in. Git-ignored |

## The target repository

For now the agent works on this repository and opens pull requests here. The root
`.agent.json` limits what that means: it may edit only `poc/sample_site/`, it may not
touch that folder's tests, and the only command it can run is the sample site's test
command. To point it at a real project later, set `TARGET_REPO` and `GITHUB_REPO`,
and give that project its own `.agent.json`.

The agent can read the whole repository, including this file. That is acceptable
here, because every task names its problem anyway.

## Running the guardrail tests

These need nothing installed: `tools.py` runs on the standard library alone, and the
suite loads it directly rather than through ADK. From the repository root:

```powershell
python -m unittest discover -s poc/tests -q
```

CI runs the same suite, plus `ruff check .`, on every push and pull request. It does
not run the sample site's own tests, because a bug is deliberately planted there
before a demonstration and a red result is the expected state.

## Running the agent

ADK runs inside Docker. On the development machine used here, Windows Smart App
Control blocks the compiled Python packages ADK depends on; Linux containers are not
affected. Anyone without that restriction can use a plain virtual environment
instead.

1. Copy `fix_agent/.env.example` to `fix_agent/.env` and add your own `GITHUB_TOKEN`.
2. Put the key for the service account
   `fix-agent@ai-sdlc-515307.iam.gserviceaccount.com` (role: Vertex AI User) at
   `poc/secrets/fix-agent-key.json`. That folder is git-ignored. Get the key from the
   project owner, and never commit or paste it.
3. Clone the repository the agent will work on, and start the container. From `poc/`:

```powershell
git clone https://github.com/dipesharma29/agentic-ai-sdlc.git workspace\agentic-ai-sdlc
```

```powershell
docker compose up --build
```

Then either the chat UI at http://localhost:8000, choosing `fix_agent`, or the API:

```powershell
python call_agent.py "The About link on the home page is broken. Fix it."
```

```powershell
python call_agent.py --approve <session_id>
```

Under the hood: `POST /apps/fix_agent/users/<user>/sessions/<id>` creates a session,
`POST /run` sends the task, and approval is a `functionResponse` to
`adk_request_confirmation` carrying `{"confirmed": true}`.

Restart the container after editing `.env`:

```powershell
docker compose up -d --force-recreate
```

## Practising on the sample site

[../docs/TESTING_THE_AGENT.md](../docs/TESTING_THE_AGENT.md) has the full loop: how to
plant a bug the agent can actually see, what to check afterwards, and how to reset
between runs. Two rules catch most mistakes — the bug has to be committed and pulled
into the agent's clone, and a test has to catch it, because `run_tests` is how the
agent proves its own work.
