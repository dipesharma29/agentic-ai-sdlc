# STATE

**Last updated:** 25 Nov 2026

What is actually true right now. Where something is unverified, it says so.
Read this before resuming work; trust it over the READMEs.

---

## At a glance

| | |
|---|---|
| Active line | **Fix Agent** — `poc/` |
| Parked | Requirements Agent — `prototype/` |
| Deadline | MVP in ~20 days from 25 Nov 2026 (Prachi) |
| Blocking | Nothing external. Docker Desktop must be running |
| Outstanding claim | **Closed 25 Nov** — a model-driven run went end to end and merged as PR #1 |

---

## Verified by running it, 25 Nov 2026

| Check | Result |
|---|---|
| Service-account key authenticates | ✅ Google issued an access token |
| Vertex AI reachable | ✅ `gemini-3.5-flash-lite`, location `global`, returned a completion (7 in / 1 out) |
| GitHub token | ✅ authenticates as `dipesharma29`; push + admin on `dipesharma29/agentic-ai-sdlc`, so it can branch and open PRs |
| Sandbox test command | ✅ runs: 3 tests, **1 failure** — the planted `abuot.html` typo. That failure is correct and must stay |
| Tool guardrails | ✅ traversal refused, edit-before-branch refused, protected paths refused, paths outside `editable_paths` refused |
| `poc/fix_agent/tools.py` | ✅ imports on the standard library alone |
| `poc/docker-compose.yml` | ✅ valid |
| Docker | installed (29.7.2, compose v5.4.0) — **daemon was not running** at time of check |

Earlier versions of the README said billing was not linked and Gemini calls would not work.
**That was true then and is false now**; the call above is the evidence.

---

## Configuration, and where it must live

| What | Where | Notes |
|---|---|---|
| Agent settings | `poc/fix_agent/.env` | **Only** place `docker-compose.yml` reads. A `.env` at the repo root is ignored by everything |
| GCP key | `poc/secrets/fix-agent-key.json` | git-ignored twice over (`poc/secrets/`, `*-key.json`) |
| Repo the agent edits | `poc/workspace/agentic-ai-sdlc/` | A separate clone, git-ignored. Not this working tree |
| GCP project | `ai-sdlc-515307` | service account `fix-agent@ai-sdlc-515307.iam.gserviceaccount.com`, role Vertex AI User |
| Jira | project **KAN** on `itmcsystems-team-r6zdxryt.atlassian.net` | KAN-4 epic; KAN-5/6/7 history; KAN-8 agent input. Not wired into the Fix Agent |

---

## Built

**Fix Agent** — `poc/fix_agent/`

- `agent.py`: one ADK `Agent`, 9 tools, no sub-agents. `commit_and_open_pr` is wrapped in
  `FunctionTool(..., require_confirmation=True)`, so ADK pauses for a human.
- `tools.py`: the 9 tools and every guardrail, in code. Standard library only.
- `poc/call_agent.py`: drives it over ADK's REST API, including the approval round trip.
- `poc/sample_site/`: the sandbox target — small HTML site, 3 tests, two planted issues.
- Docker: `python:3.12-slim` + git, `adk web` on :8000, ADK pinned to 2.15.0.

**Not built:** any test suite for the agent's own tools. The 25 Nov simulated run in Docker
was done by hand, not by a suite that can be re-run.

---

## Not proven

1. **Only one task, one language, one run.** A single success is not a measurement.
2. **The second planted task was never attempted** — the contact form's email field, which
   has no test and would require the agent to write one.
3. **Scope control is unproven.** The one real run fixed more than it was asked to.
4. **`search_code` reads every file in the repo** on each call. Fine for the 30-file
   sandbox; untested on anything large.
5. **Only one language proven.** The design claims language-agnosticism and the mechanism
   supports it, but only the Python/unittest sandbox has been run.

---

## Fixed on 25 Nov, worth knowing

Found by reading the code and verified by running it:

- `call_agent.py` raised `IndexError` when run with no arguments; it now prints usage.
- `tools.py` defaulted `TARGET_REPO` to `/app/poc/workspace/agent-poc-sandbox`, a path that
  no longer exists anywhere. Now matches `.env.example` and compose.
- `commit_and_open_pr` called the GitHub PR API without a try/except — an HTTP error would
  escape as an exception instead of the `{"status": "error"}` dict every other tool returns,
  after the branch was already pushed. It now reports `pushed: True` with the reason, so the
  work is not lost and a human can finish by hand.
- `prototype/requirements.txt` pinned nothing; it now matches the POC's `google-adk==2.15.0`.
- Added `.gitattributes` (`eol=lf`). The agent commits from a Linux container onto a Windows
  checkout; without it every agent PR shows whole files as changed and buries the real diff.

---

## First end-to-end run — 25 Nov 2026

Task: *"The about page has a malformed closing tag. Find it and fix it."* A `</htmll>` typo
was planted in `about.html`, committed and pushed, and pulled into the clone.

The agent branched `agent/fix-about-page-malformed-tag`, found it, fixed it, took the suite
from 2 failures to 0, paused for approval, and opened
[PR #1](https://github.com/dipesharma29/agentic-ai-sdlc/pull/1), since merged.

**It also fixed a bug nobody asked for.** The diff changed two files: `about.html`
(`</htmll>` → `</html>`, the task) and `index.html` (`abuot.html` → `about.html`, the
pre-existing planted link). Both fixes are correct and the agent's report was accurate, but
the scope was wider than the task.

The cause is a tension in its instruction: *"Change what the task needs, nothing unrelated"*
against *"run_tests. On failure, diagnose from the output and fix."* With an unrelated
failure already in the baseline, the agent cannot tell its job from "make the suite green".
Worth deciding deliberately — see [TODO.md](TODO.md).

**Both originally planted sandbox issues are now fixed**, so the suite is green (4 tests,
OK) and any further run needs a freshly planted bug. See
[TESTING_THE_AGENT.md](TESTING_THE_AGENT.md).

## The trap this setup has

**The agent does not see your working tree.** It reads `TARGET_REPO`, a separate clone at
`poc/workspace/agentic-ai-sdlc/`. On 25 Nov a typo was planted in
`poc/sample_site/about.html` in the working tree and the agent correctly reported no such
problem -- it was reading a different copy of that file, at commit `dd04234`.

Two things follow, and both bit at once:

1. **A bug must be committed and present in the clone before the agent can see it.** An
   uncommitted edit exists on no branch and in no clone.
2. **Pick a bug the tests can catch.** `</htmll>` is invisible to the sandbox suite, so even
   a correct fix would prove nothing -- `run_tests` is how the agent verifies itself.

Fixed so it cannot happen silently again: `search_code` with no matches and `read_file` on a
missing file now report the checkout path and commit, and the agent's instruction tells it to
say so when it concludes something is not there.

## Parked: Requirements Agent — `prototype/`

Turns a vague request or meeting transcript, plus the spring-petclinic Java code, into an
approved user story. 6 tools, including Jira history search and story save.

Done: agent code (local code search, not RAG), Docker, Jira sample tickets, PetClinic fork,
JDK 21. Not done: RAG comparison, Agent Engine / Cloud Run deployment, its own Jira token.
Model calls are no longer blocked, but it has not been run against Vertex.

Do not extend it while the Fix Agent is the active line.
