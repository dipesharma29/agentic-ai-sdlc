# ARCHITECTURE

How the Fix Agent is put together, and why each piece is shaped the way it is.
For current status see [STATE.md](STATE.md); for working rules see [AGENTS.md](../AGENTS.md).

---

## 1. The shape

```
  you ──POST /run──► ADK server (Docker, :8000)
                          │
                          ▼
                     fix_agent  ── Gemini on Vertex AI
                          │
                          ▼  (9 tools, all guarded)
          poc/workspace/agentic-ai-sdlc   ← a separate clone
                          │
         branch agent/* → edit → run tests → show diff
                          │
                   [ HUMAN CONFIRMS ]
                          │
                          ▼
              push + open PR ──► a human reviews and merges
```

**One agent.** Not a planner plus a coder plus a tester. The brief asked for one, and one
is also the honest unit of evaluation: if it fails, the failure has one address.

**Two processes, one repo.** The container edits a *separate clone* at
`poc/workspace/agentic-ai-sdlc/`, not the working tree you have open. The agent cannot
disturb the files you are editing, and its `git status` is its own.

---

## 2. The nine tools

| Tool | Does | Refuses |
|---|---|---|
| `list_files` | repo tree, skipping `.git`, `node_modules`, build dirs | paths outside the repo |
| `search_code` | keyword hits, ranked by how many words match | an empty query |
| `read_file` | first 400 lines, numbered | paths outside the repo |
| `edit_file` | one exact find-and-replace | matches ≠ 1; protected or non-editable paths; no `agent/` branch |
| `create_file` | a new file | overwriting an existing file; same path rules |
| `run_tests` | **only** the repo's `test_command` | anything else; times out at 300s |
| `create_branch` | `agent/<slug>` from `BASE_BRANCH` | a dirty working tree |
| `show_changes` | the uncommitted diff | — |
| `commit_and_open_pr` | commit, push, open PR | not on `agent/*`; nothing to commit |

Every one returns a dict and never raises. The model reads `message` and corrects itself;
an exception would just end the turn.

---

## 3. Where the authority sits

The model chooses *what* to do. It cannot widen *what is possible*. Five limits, all in
`poc/fix_agent/tools.py`:

1. **Containment.** `_inside_repo` resolves the path and refuses anything that is not under
   `REPO`. `.resolve()` first, so `..` and symlinks are collapsed before the check.
2. **Editable paths.** If `.agent.json` sets `editable_paths`, everything else is read-only.
   The root config sets `poc/sample_site/`, so the agent can read this whole repo and change
   almost none of it.
3. **Protected paths.** `.agent.json` itself, the sandbox's `tests/`, `.github/`, `.git/`.
   `.git/` is appended in code regardless of config.
4. **Exact, unique edits.** `old_text` must appear exactly once. A model quoting from memory
   is refused rather than guessed at, and an ambiguous anchor cannot silently hit the wrong
   line.
5. **Branch discipline.** No edit happens unless the branch starts with `agent/`, and there
   is no merge tool at all.

**One command exists.** `run_tests` executes the list in `test_command` with
`subprocess.run` — a list, so no shell, so nothing to inject into. It is the only command
the agent can cause to run.

Each of those six is covered by `poc/tests/test_guardrails.py`, which attempts the
forbidden action and asserts the refusal. That matters more than it sounds: a guardrail
is only load-bearing while it still works, and reading the code is not evidence that it
does. The suite runs in CI on every push.

### The human gate

`commit_and_open_pr` is wrapped in `FunctionTool(..., require_confirmation=True)`. ADK
emits an `adk_request_confirmation` call and stops. Nothing leaves the machine until a
human answers — in the chat UI, or as a `functionResponse` with `{"confirmed": true}`
from `call_agent.py --approve`.

That is the only outward-facing tool, so that is the only gate needed.

---

## 4. Why `.agent.json`

The tools know nothing about any language. Each target repo carries:

```json
{
  "test_command": ["python", "-m", "unittest", "discover", "-s", "poc/sample_site/tests", "-q"],
  "editable_paths": ["poc/sample_site/"],
  "protected_paths": [".agent.json", "poc/sample_site/.agent.json",
                      "poc/sample_site/tests/", ".github/", ".git/"]
}
```

For Java that becomes `["./mvnw", "-q", "test"]`; for Node, `["npm", "test"]`. The agent
code does not change. This is the whole claim to being language-agnostic, and it is the
reason the design survives pointing at spring-petclinic later.

**Two of these files exist and they are not the same thing:**

- `/.agent.json` — **active**. Used because `TARGET_REPO` is the whole repo clone. It scopes
  the agent to `poc/sample_site/` and runs the sandbox's tests from the repo root.
- `/poc/sample_site/.agent.json` — a **template**, for when the sample site is lifted out
  into its own repo. Nothing reads it today.

**A target repo's `.agent.json` must protect itself.** `test_command` is executed verbatim,
so an agent that can edit that file can run any command. Protect it by name, or put it
outside `editable_paths`. The root config does both.

---

## 5. Decisions worth knowing

**ADK runs in Docker, not a venv.** Windows Smart App Control blocks the compiled packages
ADK needs on this machine. Linux containers are unaffected. The container also gives the
agent a clean `git` and a predictable path layout (`/app` = repo root).

**The agent targets a clone, not the working tree.** Otherwise its `create_branch` would
fight whatever you have checked out, and its "dirty working tree" check would trip on your
edits.

**Edits are find-and-replace, not diffs.** A model-written diff has to be *applied* — fuzzy
matching, offset repair, silent partial application. An exact anchor either matches once or
is refused, and the failure is loud.

**No RAG, no vector store.** `search_code` is keyword ranking over the repo. For a 30-file
sandbox that is not a compromise, and nothing yet shows it failing on a real repo. Add one
when it demonstrably falls short, not before.

**ADK is pinned** (`google-adk==2.15.0`). The confirmation mechanism and the REST shapes
`call_agent.py` depends on are version-sensitive.

---

## 6. Layout

```
.agent.json              active guardrail config (what may be edited, how to test)
poc/
  fix_agent/agent.py     the ADK agent: model, instruction, tool list, human gate
  fix_agent/tools.py     the 9 tools and every guardrail. Stdlib only
  fix_agent/.env         settings — the only file compose reads (git-ignored)
  tests/                 guardrail tests: try the attack, assert the refusal
  sample_site/           practice target: HTML, CSS, its own tests
  notebooks/             the same demonstration in Google Colab
  secrets/               service-account key (git-ignored)
  workspace/             the clone the agent edits (git-ignored)
  call_agent.py          REST client: send a task, approve or reject
  Dockerfile             python:3.12-slim + git + ADK
  docker-compose.yml     mounts the repo at /app, reads fix_agent/.env
.github/workflows/ci.yml       lint and the guardrail suite
pyproject.toml                 lint configuration
docs/POC_Fix_Agent_Design.md   the design record this was built from
prototype/               PARKED: the Requirements Agent
```

---

## 7. Deliberately not built

| Not built | Why not |
|---|---|
| A second agent (testing, requirements, review) | The brief asks for one. Testing is a *tool* this agent calls |
| Vector store / RAG | Keyword search has not failed yet |
| Merge capability | A human merges. There is no code path to merge, by design |
| Jira in the Fix Agent loop | Explicitly out of scope for the POC |
| A planner or workflow engine | The instruction's numbered steps are the plan |

Each is reasonable to add once something needs it. Adding them now would be guessing.
