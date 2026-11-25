# TODO

Ordered by what unblocks the most. Status lives in [STATE.md](STATE.md).

**Deadline:** MVP ~20 days from 25 Nov 2026.

---

## 1. ~~First end-to-end run~~ — done 25 Nov 2026

Merged as PR #1. See [STATE.md](STATE.md) for what it did, including the part nobody
asked for.

---

## 2. Decide what the agent should do about unrelated failures

The 25 Nov run fixed a second, unasked-for bug because its baseline already had a failing
test and its instruction tells it to get to green. Pick one and make the instruction say it:

- [ ] **Narrow:** fix only what the task names; report other failures without touching them.
      Safer for review, but it will leave a red suite and may confuse its own verification
- [ ] **Broad:** get the suite green and list everything it changed. Fewer reruns, wider
      diffs, more for a human to check
- [ ] Either way, the instruction must stop saying both at once

## 2b. Restore a planted bug for demos

Both original sandbox issues are now fixed and the suite is green, so there is nothing to
demonstrate against.

- [ ] Plant a fresh one under `poc/sample_site/`, with a test that catches it
- [ ] Or keep a `demo/planted-bugs` branch to cherry-pick from

## 3. Second task, same repo

Proves it was not a one-line fluke. The planted issue is already there:

- [ ] *"Make the contact form's email field required and only accept valid email addresses."*
- [ ] No test covers this yet — the agent must add one, which exercises `create_file`
- [ ] Watch for the failure mode that matters: editing a test to go green. It is blocked by
      `protected_paths`, so confirm the refusal is what stops it

---

## 4. A test suite for the agent's own tools

The 25 Nov guardrail check was done by hand. It cannot be re-run, so a refactor could
quietly remove a guardrail.

- [ ] Tests for: containment, `editable_paths`, `protected_paths`, exact-match edits,
      branch requirement, `run_tests` only running `test_command`
- [ ] Stdlib `unittest`, so the container needs nothing new
- [ ] Each one should *try the attack* and assert the refusal

---

## 5. A second language

The design's central claim, still untested.

- [ ] Point `TARGET_REPO` at the spring-petclinic fork
- [ ] Give that repo an `.agent.json` with `["./mvnw", "-q", "test"]`
- [ ] Add a JDK to `poc/Dockerfile` — noted in the file already
- [ ] Expect `search_code` to be slow on a large repo; measure before optimising

---

## 6. Loose ends

- [ ] Delete the leftover `.env.example` at the repo root — untracked duplicate of
      `poc/fix_agent/.env.example`, and the file a real token once ended up in
- [ ] **Rotate the GitHub token.** It sat in a non-git-ignored file; treat it as exposed
- [ ] **The agent's clone goes stale.** `create_branch` does `git checkout <base>` with no
      fetch, so `poc/workspace/agentic-ai-sdlc` keeps branching from the `main` it was
      cloned at. Once PRs start merging, that drifts: the agent could re-fix something or
      raise a conflicting PR. Either `git -C poc/workspace/agentic-ai-sdlc pull` before each
      run, or make `create_branch` fetch first
- [ ] **The agent list shows three agents, not one.** `adk web` scans `/app/poc`
      recursively and finds the copies inside the clone, so `/list-apps` returns
      `fix_agent`, `workspace.agentic-ai-sdlc.poc.fix_agent` and
      `workspace.agentic-ai-sdlc.prototype.requirements_agent`. Always pick the plain
      `fix_agent`. Moving `workspace/` out of `poc/` would stop it
- [ ] `commit_and_open_pr` has no retry if the push succeeds and the PR call fails. It now
      reports `pushed: True` so nothing is lost, but a human has to finish by hand
- [ ] `docs/POC_Fix_Agent_Design.md` still describes a separate `agent-poc-sandbox` repo;
      the POC now targets this repo instead

---

## Not now, and why

| Idea | Why not yet |
|---|---|
| Jira in the loop | Out of scope for the POC. Revisit after an end-to-end run |
| RAG / vector store | Keyword search has not failed. Wait for it to |
| Cloud Run / Agent Engine | Laptop Docker is enough to prove the idea |
| A second agent | The brief says one. Adding one hides which part failed |
| Letting the agent merge | Never. The human gate is the point |
