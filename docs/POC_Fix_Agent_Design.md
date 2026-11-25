# POC: Single "Fix Agent" with ADK

**Status:** design agreed 25 Nov 2026. Build in progress.
**Goal (Prachi):** prove that one ADK agent can take a plain-language task through an API call, change the code, and hand the result to a human. No Jira yet. Keep it simple. **The tool must be language-agnostic**, not tied to Java.

---

## 1. What the POC does
You send a task over HTTP, for example *"The About link on the home page is broken, fix it"*. The agent finds the code in the target repo, edits it, runs that repo's tests, and opens a **pull request**. A human reviews and merges it. The agent can never merge.

## 2. Start small, then grow
| Step | Target repo | Why |
|---|---|---|
| **1 (now)** | **Simple HTML site** (`agent-poc-sandbox`): one page plus CSS, with a few tests | Fast, cheap, easy to see the change |
| 2 | Same site, harder tasks (add a section, fix a form, multi-file change) | Shows it can handle more than a one-line fix |
| 3 | A bigger repo in another language (e.g. spring-petclinic, already forked) | Proves it really is language-agnostic |

## 3. How it stays language-agnostic
The agent knows nothing about any language. Each target repo has a small **`.agent.json`** file that tells it how to test and what it must not touch:
```json
{
  "test_command": ["python", "-m", "unittest", "discover", "-s", "tests", "-q"],
  "protected_paths": [".agent.json", "tests/", ".github/"]
}
```
- For Java, `test_command` would be `["./mvnw", "-q", "test"]`.
- For Node, it would be `["npm", "test"]`.
- The agent code stays the same.

Tests are protected so the agent can't "pass" by changing the tests.

## 4. Flow
```
 You / Postman / curl
     │  POST /run   { task: "The About link is broken, fix it" }
     ▼
┌──────────── Docker container (laptop) ──────────────────────────┐
│  ADK server (adk web = chat UI + REST API on :8000)              │
│        ▼                                                        │
│  fix_agent (Gemini on Vertex AI)                                │
│   1. create_branch("agent/<name>")                              │
│   2. list_files / search_code / read_file → find the problem    │
│   3. edit_file (exact find-and-replace)    → make the change     │
│   4. run_tests (only .agent.json command)  → fail? retry (max 3) │
│   5. commit_and_open_pr  ← asks you to confirm first            │
└─────────┬────────────────────────────────┬──────────────────────┘
          ▼                                ▼
  GCP ai-sdlc-515307 (Vertex AI)     GitHub agent-poc-sandbox
  ✅ verified 25 Nov                   PR ──► HUMAN reviews & merges
```

## 5. Guardrails (enforced in code, not in the prompt)
| Tool | Guardrail |
|---|---|
| `list_files`, `search_code`, `read_file` | Paths must stay inside the target repo |
| `edit_file`, `create_file` | Exact replace only (`old_text` must match exactly once). Protected paths are refused. No deletes. |
| `run_tests` | Runs only the `test_command` from `.agent.json`, with no shell and a timeout. No other commands. |
| `create_branch` | Name must start with `agent/`. Never works on `main`. |
| `commit_and_open_pr` | Pushes only `agent/*` branches; needs human confirmation (ADK `require_confirmation`). Can't merge. GitHub token is scoped to the sandbox repo. |
| Loop | The instruction limits it to 3 fix-test attempts. |

## 6. Colab vs VS Code
ADK is ordinary Python, so it works in both. We build in **VS Code + Docker**:
- it needs a real repo, Git, tests and an HTTP endpoint;
- Docker also avoids the Smart App Control block on Dipesh's laptop;
- the same code later deploys to Agent Engine / Cloud Run.

A short Colab notebook can be added as a demo companion if Prachi wants one.

## 7. Steps
1. ✅ Design (this doc)
2. ✅ Sample HTML site + tests + planted bug
3. ✅ Fix agent code + Docker (9 tools, simulated run passed)
4. ✅ Gemini reachable (key + Vertex AI verified 25 Nov) → first fix locally still to do
5. GitHub sandbox repo + token → first real PR
6. Harder tasks → then a second language
