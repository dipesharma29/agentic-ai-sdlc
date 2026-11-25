# Agentic AI SDLC (AI DLC): GCP Prototype

A small learning prototype for ITMC's AI DLC framework on Google Cloud. Stage 1 is the **Requirements Agent**: a vague request or meeting transcript, plus the existing Java code (spring-petclinic), becomes a user story that says where the change belongs. A human approves the story before it's saved.

## Folder map
| Path | What |
|---|---|
| `AI_DLC_Understanding_and_Assessment.md` | Assessment of the ChatGPT conversation and the deck |
| `Prototype_Questions.md` | Scoping questions, decisions and open items |
| `notes/GCP_Services_Notes.md` | What each GCP service is, how we use it, cost watch-points |
| `prototype/requirements_agent/` | ADK agent (`agent.py`) and its tools (`tools.py`) |
| `prototype/inputs/` | Meeting transcript used as input |
| `prototype/output/stories/` | Approved stories when Jira isn't configured (created on first save) |
| `sources/` | Original deck, conversation export, transcript |
| `workspace/spring-petclinic/` | Local clone of the fork `dipesharma29/spring-petclinic` (git-ignored) |

## Where things live
- **GCP project:** `ai-sdlc-515307` (billing not linked yet, so Gemini calls won't work until it is).
- **Jira:** project **KAN** on `itmcsystems-team-r6zdxryt.atlassian.net`
  - Epic KAN-4: the prototype epic.
  - KAN-5, KAN-6, KAN-7: made-up past tickets (`petclinic-history`).
  - KAN-8: the vague request the agent turns into a story (`agent-input`).

## Run it locally (once billing is linked and APIs are on)
ADK runs **inside Docker**. On Dipesh's laptop, Windows Smart App Control blocks the compiled Python packages ADK needs, but Linux containers aren't affected. Teammates without that block can also use a plain Python venv (`pip install -r prototype/requirements.txt`, then `adk web` from `prototype/`).

1. Sign in once so the container can use your Google credentials:
```powershell
gcloud auth application-default login
```
2. Create your settings file (only if `prototype\requirements_agent\.env` doesn't exist yet):
```powershell
Copy-Item prototype\requirements_agent\.env.example prototype\requirements_agent\.env
```
3. Start the ADK web UI:
```powershell
cd prototype; docker compose up --build
```
Open http://localhost:8000, pick `requirements_agent`, and try:
- "Turn Jira request KAN-8 into a user story." (paste the request text if Jira isn't configured)
- "Read the meeting transcript and draft the first user story for the AI DLC framework."

## STATUS (25 Nov 2026)
Resumed. New direction from Prachi: **single-agent POC first** (task in, code fix out, via an API call). The MVP is due in about 20 days. See `docs/POC_Fix_Agent_Design.md`. The Requirements Agent below is parked.

## Current state
- **Done:** repo layout, agent code (v1: local code search instead of RAG), Docker setup (ADK 2.15.0; agent loads, tools tested), Jira sample tickets, PetClinic fork and clone, JDK 21, service notes.
- **Not done:** model calls (need billing plus the Vertex AI API), RAG comparison, Agent Engine / Cloud Run deployment, agent's own Jira token.
