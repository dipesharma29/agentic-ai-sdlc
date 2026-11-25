# Agentic AI SDLC (AI DLC): GCP Prototype

A learning prototype for ITMC's AI DLC framework on Google Cloud, built with Google ADK.

**Current line of work: the Fix Agent.** You send a plain-language task over HTTP; one agent
finds the code in a target repo, changes it, runs that repo's own tests, and opens a pull
request for a human to review. It can never merge. See
[`docs/POC_Fix_Agent_Design.md`](docs/POC_Fix_Agent_Design.md) and [`poc/README.md`](poc/README.md).

The **Requirements Agent** (a vague request or meeting transcript becomes an approved user
story) came first and is **parked** — see [Parked: Requirements Agent](#parked-requirements-agent).

**Resuming work, or an AI agent reading this?** Start with [STATE.md](docs/STATE.md) — what is
true right now — then [AGENTS.md](AGENTS.md) for how to work here.

## Folder map

Paths marked *local only* are git-ignored: they will not be in a fresh clone, and you create
them yourself.

| Path | What |
|---|---|
| [`docs/STATE.md`](docs/STATE.md) | What is built, what is verified, what is not. **Read first** |
| [`AGENTS.md`](AGENTS.md) | Rules and commands for anyone (human or AI) working on this repo |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | How the Fix Agent works and why it is shaped that way |
| [`docs/TODO.md`](docs/TODO.md) | What is next, in order |
| `poc/` | **The Fix Agent.** Agent, tools, sandbox target, Docker, REST client |
| `poc/fix_agent/` | `agent.py` and `tools.py` — 9 tools behind guardrails |
| `poc/sample_site/` | The sandbox the agent is allowed to edit: small HTML site + tests |
| `poc/call_agent.py` | Sends a task over ADK's REST API; approves or rejects the PR |
| `poc/workspace/agentic-ai-sdlc/` | *local only* — the clone the agent actually works in |
| `poc/secrets/` | *local only* — the service-account key |
| `docs/POC_Fix_Agent_Design.md` | Why the POC is shaped this way |
| `.agent.json` | Per-repo rules: how to test, what may be edited, what is protected |
| `AI_DLC_Understanding_and_Assessment.md` | Assessment of the ChatGPT conversation and the deck |
| `Prototype_Questions.md` | Scoping questions, decisions and open items |
| `notes/GCP_Services_Notes.md` | What each GCP service is, how we use it, cost watch-points |
| `prototype/requirements_agent/` | Parked: the Requirements Agent and its tools |
| `prototype/inputs/` | *local only* — meeting transcript used as input |
| `prototype/output/stories/` | *local only* — approved stories when Jira isn't configured |
| `sources/` | *local only* — original deck, conversation export, transcript |
| `workspace/spring-petclinic/` | *local only* — clone of the `dipesharma29/spring-petclinic` fork |

## How the Fix Agent stays safe

Four things, and none of them depend on the model behaving:

- **`.agent.json` decides what it may touch.** The root one lets the agent edit only
  `poc/sample_site/`, and protects `.agent.json`, the sample site's `tests/`, `.github/` and
  `.git/`. The agent cannot pass a task by rewriting the test that was failing.
- **The same file decides how to test.** `test_command` is the only command it can run, so
  the agent knows nothing about Python, Java or Node — point it at another repo and that
  repo's file tells it what to do.
- **Edits must quote the existing text exactly**, and are refused if the text appears more
  than once.
- **A human confirms before anything leaves the machine.** `commit_and_open_pr` is wrapped in
  `FunctionTool(..., require_confirmation=True)`, so ADK pauses and waits.

## Where things live

- **GCP project:** `ai-sdlc-515307`. **Working as of 25 Nov 2026** — verified by an actual
  call, not assumed: the service-account key authenticates, the Vertex AI API answers, and
  `gemini-3.5-flash-lite` at location `global` returned a completion. The billing blocker
  noted in earlier versions of this file is cleared.
- **Service account:** `fix-agent@ai-sdlc-515307.iam.gserviceaccount.com` (role: Vertex AI
  User). Its key goes at `poc/secrets/fix-agent-key.json`, which is git-ignored. Get it from
  the project owner; never commit or paste it.
- **Jira:** project **KAN** on `itmcsystems-team-r6zdxryt.atlassian.net`
  - Epic KAN-4: the prototype epic.
  - KAN-5, KAN-6, KAN-7: made-up past tickets (`petclinic-history`).
  - KAN-8: the vague request the Requirements Agent turns into a story (`agent-input`).

## Run the Fix Agent

ADK runs **inside Docker**. On Dipesh's laptop, Windows Smart App Control blocks the compiled
Python packages ADK needs; Linux containers are not affected.

Full instructions, including the approval round trip, are in [`poc/README.md`](poc/README.md).
The short version, from `poc/`:

```powershell
Copy-Item fix_agent\.env.example fix_agent\.env
```
```powershell
git clone https://github.com/dipesharma29/agentic-ai-sdlc.git workspace\agentic-ai-sdlc
```
```powershell
docker compose up --build
```

Then the chat UI at http://localhost:8000 (pick `fix_agent`), or over the API:

```powershell
python call_agent.py "The About link on the home page is broken. Fix it."
```
```powershell
python call_agent.py --approve <session_id>
```

## Status — 25 Nov 2026

New direction from Prachi: **single-agent POC first** — task in, code fix out, through an API
call. No Jira in the loop yet. Keep it simple, and keep it language-agnostic. The MVP is due
in about 20 days.

**Fix Agent**

- **Done:** agent and 9 tools; `.agent.json` guardrails; Docker on ADK 2.15.0; sandbox site
  with planted issues; REST client with the approval round trip.
- **Verified 25 Nov**, in Docker, without Gemini: all 9 tools passed a simulated run. The
  agent could not edit before creating a branch, could not touch `tests/` or anything outside
  the repo, and edits matching more than once were refused. The fix took the sample site's
  tests from failing to passing, and the commit happened locally.
- **Verified 25 Nov, live:** the service-account key at `poc/secrets/fix-agent-key.json`
  authenticates; a real Vertex AI call with `gemini-3.5-flash-lite` at location `global`
  returned a completion; the `GITHUB_TOKEN` in `poc/fix_agent/.env` authenticates as
  `dipesharma29` with push rights on this repo, so it can create branches and open PRs.
- **Not done:** an end-to-end run driven by the model. Every prerequisite now checks out, but
  no task has been taken from plain language through to an opened pull request, and no PR has
  ever been opened by the agent. That is the next thing to do, and the only claim still
  outstanding.

## Parked: Requirements Agent

A vague request or meeting transcript, plus the existing Java code (spring-petclinic), becomes
a user story that says where the change belongs. A human approves the story before it is saved.

- **Done:** repo layout, agent code (v1 uses local code search instead of RAG), Docker setup
  (ADK 2.15.0; agent loads, tools tested), Jira sample tickets, PetClinic fork and clone,
  JDK 21, service notes.
- **Not done:** RAG comparison, Agent Engine / Cloud Run deployment, the agent's own Jira
  token. Model calls are no longer blocked — Vertex AI works on this project (see above) —
  but the Requirements Agent has not been run against it.

To run it, from `prototype/`: `docker compose up --build`, then
http://localhost:8000 and pick `requirements_agent`. Teammates without the Smart App Control
block can use a plain venv instead: `pip install -r prototype/requirements.txt`, then
`adk web` from `prototype/`.
