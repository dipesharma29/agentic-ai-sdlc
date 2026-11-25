# AGENTS.md

Instructions for AI coding agents working **on** this repository.

> This file follows the [agents.md](https://agents.md) convention. It is *not* about the
> agents this project builds — those are in [ARCHITECTURE.md](docs/ARCHITECTURE.md).
>
> Read [STATE.md](docs/STATE.md) before anything else: it says what is actually true right now.
> Trust it over any assumption, including the READMEs.

---

## Orientation

| | |
|---|---|
| What this is | A POC: **one** ADK agent takes a plain-language task, edits a repo, runs its tests, opens a PR |
| Active code | `poc/` |
| Parked code | `prototype/` — the Requirements Agent. Do not extend it |
| Where the agent runs | Docker, `adk web` on port 8000 |
| Where the agent *edits* | A **separate clone** at `poc/workspace/agentic-ai-sdlc/`, never this working tree |
| Model | Gemini on Vertex AI, project `ai-sdlc-515307` |

---

## Setup

ADK runs **inside Docker**. On this machine Windows Smart App Control blocks the compiled
packages ADK needs; Linux containers are unaffected. Do not try to `pip install google-adk`
into a Windows venv to "simplify" things — that is the problem this works around.

```powershell
Copy-Item poc\fix_agent\.env.example poc\fix_agent\.env
```

Then put the service-account key at `poc/secrets/fix-agent-key.json` (git-ignored; get it
from the project owner) and clone the repo the agent works on:

```powershell
git clone https://github.com/dipesharma29/agentic-ai-sdlc.git poc\workspace\agentic-ai-sdlc
```

---

## Commands

| Task | Command |
|---|---|
| Start the agent | `cd poc; docker compose up --build` |
| Chat UI | http://localhost:8000 → pick `fix_agent` |
| Send a task | `cd poc; python call_agent.py "<task>"` |
| Approve / reject | `python call_agent.py --approve <session_id>` |
| Guardrail tests | `python -m unittest discover -s poc/tests -q` |
| Lint | `ruff check .` |
| Sample-site tests | `python -m unittest discover -s poc/sample_site/tests -q` |
| Reload after `.env` edits | `docker compose up -d --force-recreate` |

The guardrail suite needs nothing installed — `tools.py` runs on the standard library
alone and the suite loads it directly. CI runs it, and `ruff`, on every push and pull
request. It does not run the sample-site suite: a bug is planted there on purpose
before a demonstration, so a red result is the expected state.

---

## Hard rules

These are the security model. Breaking one is a defect even if everything still runs.

### 1. Guardrails live in code, never in the prompt

Every limit on the agent is enforced in `poc/fix_agent/tools.py`: path containment,
editable paths, protected paths, exact-match edits, the single allowed command, the
`agent/` branch requirement. A prompt instruction is not a guardrail — a model can talk
itself past one. If you add a tool, add its check in the tool.

### 2. The agent never merges, and never acts outside `agent/*`

`create_branch` is the only way work starts; `edit_file` and `create_file` refuse unless the
current branch starts with `agent/`. There is no merge tool and there must not be one.
A human reviews and merges every PR.

### 3. `commit_and_open_pr` stays behind `require_confirmation=True`

It is wrapped in `FunctionTool(..., require_confirmation=True)` in `agent.py`, so ADK pauses
and waits for a human. Removing that wrapper lets a model push to GitHub unattended.

### 4. The target repo's `.agent.json` is the only source of repo-specific behaviour

`test_command`, `protected_paths`, and optional `editable_paths`. The agent code knows
nothing about Python, Java or Node — that is what makes it language-agnostic. Never
hard-code a path, a framework or a test runner into the tools.

**A target repo's `.agent.json` must protect itself.** `test_command` is executed, so an
agent that can rewrite `.agent.json` can run any command. Either list `.agent.json` in
`protected_paths`, or set `editable_paths` so it is out of reach. This repo's root config
does both.

### 5. Never edit tests to make them pass

Tests state the required behaviour. `protected_paths` enforces this for the sandbox; apply
the same judgement to any repo. If a test looks wrong, say so and stop.

### 6. Secrets never enter the repo or a model's context

`poc/secrets/`, `*-key.json` and `.env` are git-ignored. Do not print token or key values,
do not paste them into prompts, and never put a real value in `.env.example` — that file
is committed. Placeholders only.

---

## Conventions

- **Stdlib only** in `poc/fix_agent/tools.py` and `poc/call_agent.py`. The container
  installs ADK and nothing else; a new dependency is a deliberate change to
  `poc/requirements.txt` and the image.
- **Every tool returns a dict**, never raises: `{"status": "success"|"error"|..., ...}`.
  The model reads the message and corrects itself. A raised exception is a dead end.
- **Tool docstrings are the model's API documentation.** ADK builds the function-calling
  schema from the signature and the `Args:` block. A vague docstring is a bug.
- **Short, plain names.** Match the existing style; this codebase is deliberately small.

---

## Before you call it done

1. `python -m unittest discover -s poc/tests -q` passes. That is the guardrails —
   traversal, the branch requirement, protected paths, `editable_paths`, exact-match
   edits, and `run_tests` running only `test_command`.
2. `ruff check .` is clean.
3. The sample-site command still runs, and a planted bug still fails if one is planted
   (see [STATE.md](docs/STATE.md) for the current baseline).
4. [STATE.md](docs/STATE.md) updated if what is built or verified changed.
5. **Say what you did not verify.** An unverified claim stated as fact costs the next
   person the time to discover it. This repo has been wrong about its own status before.
