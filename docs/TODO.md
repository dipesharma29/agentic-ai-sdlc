# What is next

Ordered by what unblocks the most. Current status lives in [STATE.md](STATE.md).

**Target date:** MVP approximately 20 days from 25 November 2026.

---

## 1. Decide what the agent does about unrelated failures

The first live run fixed a second, unasked-for bug, because its baseline already
had a failing test and its instruction tells it to reach green. Pick one of these
and make the instruction say only that:

- [ ] **Narrow.** Fix what the task names; report other failures without touching
      them. Safer to review, but it leaves a red suite and complicates the agent's
      own verification.
- [ ] **Broad.** Reach green and list everything changed. Fewer repeat runs, wider
      diffs, more for a human to check.

Either way, the instruction must stop asserting both at once.

## 2. A second task against the same repository

Proves the first run was not a one-line fluke.

- [ ] *"Make the contact form's email field required and only accept valid email
      addresses."*
- [ ] No test covers this yet, so the agent has to write one. That exercises
      `create_file`, which the first run never touched.
- [ ] Watch for the failure that matters: weakening a test to reach green. It is
      blocked by `protected_paths`, and the guardrail suite asserts the refusal, so
      confirm the agent handles the refusal sensibly rather than looping on it.

## 3. A second language

The design's central claim, still untested.

- [ ] Point `TARGET_REPO` at the spring-petclinic fork.
- [ ] Give that repository an `.agent.json` with `["./mvnw", "-q", "test"]`.
- [ ] Add a JDK to `poc/Dockerfile`; the file already notes where.
- [ ] Expect `search_code` to be slow on a large repository. Measure before
      optimising.

## 4. Run the Colab notebook end to end

Every cell compiles and the ADK shapes were checked against 2.15.0, but nobody has
taken it through a complete run in Colab yet.

- [ ] Grant the reviewer **Vertex AI User** on `ai-sdlc-515307` and collaborator
      access on the repository.
- [ ] Confirm a planted bug is live on `main` first, or the notebook has nothing to
      demonstrate against.

---

## Known issues

- [ ] **Rotate the GitHub token.** It was written into a loose file on disk that was
      not covered by `.gitignore`. It never entered a commit — the history has been
      checked — but it should be treated as exposed and replaced.
- [ ] **The agent's clone goes stale.** `create_branch` checks out the base branch
      without fetching, so `poc/workspace/agentic-ai-sdlc` keeps branching from the
      commit it was cloned at. Once pull requests start merging, that drifts, and the
      agent could re-fix something already fixed or raise a conflicting change. Either
      pull before each run, or make `create_branch` fetch first.
- [ ] **The agent list shows three entries, not one.** `adk web` scans `/app/poc`
      recursively and finds the copies inside the clone, so it offers `fix_agent`,
      `workspace.agentic-ai-sdlc.poc.fix_agent` and
      `workspace.agentic-ai-sdlc.prototype.requirements_agent`. Always choose the plain
      `fix_agent`. Moving `workspace/` out of `poc/` would stop it.
- [ ] **`commit_and_open_pr` has no retry** if the push succeeds and the pull-request
      call fails. It reports `pushed: true` so no work is lost, but a human has to
      finish by hand.
- [ ] **`docs/POC_Fix_Agent_Design.md` is a design record**, written before the POC
      was built. It describes intent at that point, not the current shape.

---

## Deliberately not doing yet

| Idea | Why not |
|---|---|
| Jira in the loop | Out of scope for the POC |
| RAG or a vector store | Keyword search has not failed yet. Wait until it does |
| Cloud Run or Agent Engine | Local Docker is enough to prove the idea |
| A second agent | The brief asks for one. A second hides which part failed |
| Letting the agent merge | Never. The human gate is the point of the design |
