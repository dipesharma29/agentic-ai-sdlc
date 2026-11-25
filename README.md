# Agentic AI SDLC: a GCP prototype

A prototype for ITMC's AI DLC framework on Google Cloud, built with the Google Agent
Development Kit.

**Current line of work: the Fix Agent.** You send a plain-language task; one agent
finds the code in a target repository, changes it, runs that repository's own tests,
and opens a pull request for a human to review. It cannot merge.

The **Requirements Agent** — turning a vague request or a meeting transcript into an
approved user story — came first and is now parked. See
[Parked: Requirements Agent](#parked-requirements-agent).

**Picking the work up again?** Start with [docs/STATE.md](docs/STATE.md), which says
what is true right now, then [AGENTS.md](AGENTS.md) for how to work in this repository.

---

## How the Fix Agent stays safe

Four limits, none of which depends on the model behaving well:

- **`.agent.json` decides what the agent may touch.** The root configuration lets it
  edit only `poc/sample_site/`, and protects `.agent.json` itself, the sample site's
  tests, `.github/` and `.git/`. It cannot pass a task by rewriting the test that was
  failing.
- **The same file decides how to test.** `test_command` is the only command the agent
  can run, with no shell. The agent itself knows nothing about Python, Java or Node —
  point it at another repository and that repository's file tells it what to do.
- **Edits must quote the existing text exactly**, and are refused if the text appears
  more than once. An ambiguous replacement is a guess.
- **A human confirms before anything leaves the machine.** `commit_and_open_pr` is
  wrapped in `FunctionTool(..., require_confirmation=True)`, so the framework pauses
  and waits.

Each of those is enforced in `poc/fix_agent/tools.py` and covered by a test in
`poc/tests/test_guardrails.py` that attempts the action and asserts the refusal.

```powershell
python -m unittest discover -s poc/tests -q
```

---

## Where things are

| Path | What |
|---|---|
| [`docs/STATE.md`](docs/STATE.md) | What is built, what is verified, what is not. Read first |
| [`AGENTS.md`](AGENTS.md) | Rules and commands for anyone, human or AI, working here |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | How the Fix Agent works, and why it is shaped that way |
| [`docs/TODO.md`](docs/TODO.md) | What is next, in order |
| [`docs/TESTING_THE_AGENT.md`](docs/TESTING_THE_AGENT.md) | How to plant a bug and test the agent yourself |
| [`docs/POC_Fix_Agent_Design.md`](docs/POC_Fix_Agent_Design.md) | The design record, written before the build |
| [`poc/`](poc/README.md) | The Fix Agent: agent, tools, guardrail tests, practice target, Docker, REST client |
| `poc/fix_agent/` | `agent.py` and `tools.py` — nine tools behind the guardrails |
| `poc/tests/` | The guardrail tests |
| `poc/sample_site/` | The practice target the agent is allowed to edit |
| `poc/notebooks/` | The same demonstration in Google Colab, with no local install |
| `.agent.json` | Per-repository rules: how to test, what may be edited, what is protected |
| `.github/workflows/ci.yml` | Lint and guardrail tests on every push and pull request |
| `prototype/` | Parked: the Requirements Agent |

Some paths are git-ignored and will not be in a fresh clone: `poc/workspace/` (the
clone the agent works in), `poc/secrets/` (the service-account key), and `sources/`.

---

## Running it

ADK runs inside Docker. On the development machine used here, Windows Smart App
Control blocks the compiled Python packages ADK depends on; Linux containers are not
affected, and anyone without that restriction can use a plain virtual environment.

Full instructions, including the approval round trip, are in
[`poc/README.md`](poc/README.md). The short version, from `poc/`:

```powershell
Copy-Item fix_agent\.env.example fix_agent\.env
```

```powershell
git clone https://github.com/dipesharma29/agentic-ai-sdlc.git workspace\agentic-ai-sdlc
```

```powershell
docker compose up --build
```

Then the chat UI at http://localhost:8000, choosing `fix_agent`, or over the API:

```powershell
python call_agent.py "The About link on the home page is broken. Fix it."
```

```powershell
python call_agent.py --approve <session_id>
```

To show it to someone without a local setup, `poc/notebooks/fix_agent_colab.ipynb`
runs the whole loop in Google Colab. Whoever runs it uses their own credentials: a
Google account with Vertex AI User on `ai-sdlc-515307`, and their own GitHub token in
their own Colab secrets. Nothing is shared.

---

## Infrastructure

- **GCP project:** `ai-sdlc-515307`. Verified working by an actual call, not assumed:
  the service-account key authenticates, the Vertex AI API answers, and
  `gemini-3.5-flash-lite` at location `global` returns a completion.
- **Service account:** `fix-agent@ai-sdlc-515307.iam.gserviceaccount.com`, role Vertex
  AI User. Its key belongs at `poc/secrets/fix-agent-key.json`, which is git-ignored.
  Get it from the project owner; never commit or paste it.
- **Jira:** project KAN on `itmcsystems-team-r6zdxryt.atlassian.net`. Sample tickets
  only, and not yet wired into the Fix Agent.

---

## Status

A plain-language task has gone end to end: the agent branched, diagnosed the problem,
fixed it, took the test suite from failing to passing, paused for approval, and opened
[pull request #1](https://github.com/dipesharma29/agentic-ai-sdlc/pull/1), since merged.

It also fixed a second bug it had not been asked about. Both changes were correct, but
the scope was wider than the request, and only the diff showed that. The cause and the
decision it needs are written up in [docs/STATE.md](docs/STATE.md) and
[docs/TODO.md](docs/TODO.md).

What is not yet proven: more than one task, more than one language, and scope control.
Capability is no longer the open question; predictability is.

---

## Parked: Requirements Agent

A vague request or a meeting transcript, together with existing Java code
(spring-petclinic), becomes a user story that says where the change belongs. A human
approves the story before it is saved.

Built: the repository layout, the agent and its tools (local keyword search rather than
RAG), the Docker setup, Jira sample tickets, the PetClinic fork and clone, JDK 21.
Not built: a RAG comparison, deployment to Agent Engine or Cloud Run, and the agent's
own Jira credentials. Model calls are no longer blocked, but it has not been run
against Vertex AI.

To run it, from `prototype/`: `docker compose up --build`, then
http://localhost:8000 and choose `requirements_agent`.
