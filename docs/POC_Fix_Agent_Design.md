# Design record: a single Fix Agent on ADK

> **This is a design record, written before the POC was built.** It states the
> intent and the reasoning behind the shape of the system. For what exists and
> works today, read [STATE.md](STATE.md); for how the built system is put
> together, read [ARCHITECTURE.md](ARCHITECTURE.md).
>
> Agreed 25 November 2026.

**Goal.** Prove that one ADK agent can take a plain-language task through an API
call, change the code, and hand the result to a human for review. No Jira in the
loop. Keep it simple. The tool must be language-agnostic rather than tied to Java.

---

## 1. What the POC does

You send a task over HTTP — for example *"The About link on the home page is
broken, fix it"*. The agent finds the code in the target repository, edits it, runs
that repository's own tests, and opens a pull request. A human reviews and merges.
The agent can never merge.

## 2. Start small, then grow

| Step | Target | Why |
|---|---|---|
| 1 | A small HTML site with a few tests | Fast and cheap, and the change is easy to see |
| 2 | The same site, harder tasks: add a section, fix a form, change several files | Shows it handles more than a one-line fix |
| 3 | A larger repository in another language, such as the spring-petclinic fork | Proves the language-agnostic claim |

## 3. How it stays language-agnostic

The agent knows nothing about any language. Each target repository carries a small
`.agent.json` that tells it how to test and what it must not touch:

```json
{
  "test_command": ["python", "-m", "unittest", "discover", "-s", "tests", "-q"],
  "protected_paths": [".agent.json", "tests/", ".github/"]
}
```

For Java, `test_command` becomes `["./mvnw", "-q", "test"]`; for Node,
`["npm", "test"]`. The agent's own code does not change.

Tests are protected so the agent cannot pass a task by weakening the test that was
failing. `.agent.json` protects itself for the same reason: `test_command` is
executed, so an agent able to rewrite that file could run any command it liked.

## 4. Intended flow

```
  caller
     │  POST /run   { task: "The About link is broken, fix it" }
     ▼
┌──────────── Docker container ───────────────────────────────────┐
│  ADK server: chat UI and REST API on port 8000                  │
│        ▼                                                        │
│  fix_agent, backed by Gemini on Vertex AI                       │
│   1. create_branch("agent/<name>")                              │
│   2. list_files / search_code / read_file   find the problem    │
│   3. edit_file, an exact find-and-replace   make the change     │
│   4. run_tests, the .agent.json command     retry on failure    │
│   5. commit_and_open_pr                     asks a human first  │
└─────────┬────────────────────────────────┬──────────────────────┘
          ▼                                ▼
   Vertex AI, ai-sdlc-515307         GitHub: pull request
                                     a human reviews and merges
```

## 5. Guardrails, enforced in code rather than in the prompt

| Tool | Guardrail |
|---|---|
| `list_files`, `search_code`, `read_file` | Paths must resolve inside the target repository |
| `edit_file`, `create_file` | Exact replacement only, matching exactly once. Protected and non-editable paths refused. No deletions |
| `run_tests` | Runs only the `test_command` from `.agent.json`, with no shell and a timeout. No other command can be run |
| `create_branch` | The branch name is forced under the `agent/` prefix. Work never happens on the base branch |
| `commit_and_open_pr` | Pushes only `agent/*` branches, and requires human confirmation through ADK. There is no merge tool |
| The loop | The instruction limits the agent to three fix-and-test attempts |

A limit written in the prompt is not a guardrail, because a model can talk itself
past one. Each of the above is a check in `poc/fix_agent/tools.py`, and each is
covered by a test in `poc/tests/test_guardrails.py` that attempts the action and
asserts the refusal.

## 6. Why Docker and an editor, rather than a notebook

ADK is ordinary Python and runs in both. The build happens in an editor with Docker
because the agent needs a real repository, Git, a test runner and an HTTP endpoint,
and because the same code later deploys to Agent Engine or Cloud Run. Docker also
sidesteps a Windows Smart App Control restriction on the development machine used
here, which blocks the compiled packages ADK depends on.

A Colab notebook was added afterwards as a demonstration companion, so the whole
loop can be shown to someone else with no local installation:
`poc/notebooks/fix_agent_colab.ipynb`.
