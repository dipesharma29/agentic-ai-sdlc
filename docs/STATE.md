# Project state

**Last updated:** 25 November 2026

What is true right now. Where something is unproven, this file says so.
Read it before resuming work, and trust it over the READMEs.

---

## At a glance

| | |
|---|---|
| Active line of work | Fix Agent — `poc/` |
| Parked | Requirements Agent — `prototype/` |
| Target date | MVP approximately 20 days from 25 November 2026 |
| External blockers | None. Docker Desktop must be running to use the local chat UI |
| End-to-end run | Done. A plain-language task reached a reviewed, merged pull request |

---

## Verified by running it

Each row below was checked by executing something, not by reading the code.

| Check | Result |
|---|---|
| Service-account key | Authenticates; Google issues an access token |
| Vertex AI | `gemini-3.5-flash-lite`, location `global`, returned a completion |
| GitHub token | Authenticates; has push access, so the agent can branch and open pull requests |
| Guardrail suite | 34 tests, all passing — `python -m unittest discover -s poc/tests -q` |
| Lint | Clean — `ruff check .` |
| Sample-site suite | 4 tests, 1 failure. The failure is the planted demo bug and is meant to be there |
| `poc/fix_agent/tools.py` | Imports on the standard library alone, with no ADK present |
| `poc/docker-compose.yml` | Valid |

An earlier version of the README said billing was not linked and that model calls
would fail. That was true when written and is no longer true; the Vertex AI call
above is the evidence.

---

## Configuration, and where it has to live

| What | Where | Notes |
|---|---|---|
| Agent settings | `poc/fix_agent/.env` | The only location `docker-compose.yml` reads. A `.env` at the repository root is ignored by everything |
| Service-account key | `poc/secrets/fix-agent-key.json` | Git-ignored twice over, by folder and by `*-key.json` |
| Repository the agent edits | `poc/workspace/agentic-ai-sdlc/` | A separate clone, git-ignored. Not this working tree |
| GCP project | `ai-sdlc-515307` | Service account `fix-agent@ai-sdlc-515307.iam.gserviceaccount.com`, role Vertex AI User |

---

## What is built

**Fix Agent** — `poc/fix_agent/`

- `agent.py`: one ADK agent with nine tools and no sub-agents. `commit_and_open_pr`
  is wrapped in `FunctionTool(..., require_confirmation=True)`, so the framework
  pauses for a human before anything is pushed.
- `tools.py`: the nine tools and every guardrail, enforced in code. Standard
  library only, so the container needs nothing beyond ADK itself.
- `poc/tests/test_guardrails.py`: 34 tests, each of which attempts something the
  agent must not be able to do and asserts the refusal — path traversal, editing
  outside the allowed paths, touching protected files, editing without a branch,
  ambiguous replacements, and running anything other than the configured test
  command.
- `poc/call_agent.py`: drives the agent over ADK's REST API, including the
  approval round trip.
- `poc/sample_site/`: the practice target. A small HTML site with its own tests.
- `poc/notebooks/fix_agent_colab.ipynb`: the same demonstration in Google Colab,
  with no local install.
- Docker: `python:3.12-slim` plus git, serving ADK on port 8000.
- CI: `.github/workflows/ci.yml` runs lint and the guardrail suite on every push
  and pull request.

---

## What is not proven

1. **One task, one language, one run.** A single success is not a measurement.
2. **Scope control.** The one live run fixed more than it was asked to; see below.
3. **Only Python and `unittest` have been exercised.** The design is
   language-agnostic and the mechanism supports it, but no second language has
   been run.
4. **`search_code` reads every file in the repository on each call.** Fine for a
   thirty-file sandbox, untested on anything large.
5. **The Colab notebook has not been run to completion.** Every code cell
   compiles and the ADK call shapes were checked against version 2.15.0, but the
   notebook has not yet been taken through a full run in Colab by a second person.

---

## The first end-to-end run

Task: *"The about page has a malformed closing tag. Find it and fix it."* The typo
was planted, committed, pushed, and pulled into the agent's clone.

The agent created `agent/fix-about-page-malformed-tag`, located the typo, fixed it,
took the suite from two failures to none, paused for approval, and opened
[pull request #1](https://github.com/dipesharma29/agentic-ai-sdlc/pull/1), since merged.

**It also fixed a bug nobody asked for.** The diff changed two files: `about.html`,
which was the task, and `index.html`, which carried a separate broken link. Both
changes were correct and the agent's report was accurate — only the diff showed
that the scope was wider than the request.

The cause is a tension in the agent's own instruction: *"change what the task needs,
nothing unrelated"* against *"run the tests; on failure, diagnose and fix"*. When an
unrelated failure is already in the baseline, those two sentences disagree, and the
agent cannot tell its job from "make the suite green". This needs a deliberate
decision rather than a reworded prompt — see [TODO.md](TODO.md).

---

## A trap worth knowing about

**The agent does not see your working tree.** It reads `TARGET_REPO`, a separate
clone at `poc/workspace/agentic-ai-sdlc/`. A bug edited but not committed exists on
no branch and in no clone, so the agent correctly reports that there is no such
problem — it is reading a different copy of the file.

Two consequences:

1. A bug has to be committed and pulled into the clone before the agent can see it.
2. A test has to catch the bug, because `run_tests` is how the agent verifies itself.
   A bug no test sees means the agent is guessing.

This can no longer fail silently: `search_code` with no matches and `read_file` on a
missing file both report which checkout and commit they looked at.

---

## Parked: Requirements Agent — `prototype/`

Turns a vague request or a meeting transcript, together with the spring-petclinic
Java code, into an approved user story. Six tools, including Jira history search.

Built: the agent and its tools (local keyword search rather than RAG), Docker, Jira
sample tickets, the PetClinic fork, JDK 21. Not built: a RAG comparison, deployment
to Agent Engine or Cloud Run, and its own Jira credentials. Model calls are no longer
blocked, but it has not been run against Vertex AI.

Do not extend it while the Fix Agent is the active line of work.
