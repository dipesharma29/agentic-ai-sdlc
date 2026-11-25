# Testing the Fix Agent yourself

The repeatable loop for giving the agent a bug and checking it honestly.
First proven end to end on 25 Nov 2026 — see [STATE.md](STATE.md).

---

## Three rules a task must satisfy

Get one wrong and the run fails in a way that looks like the agent is broken.

1. **The bug must be committed and present in the clone.** The agent reads
   `poc/workspace/agentic-ai-sdlc/`, not your working tree. An uncommitted edit is
   invisible to it, and `create_branch` also refuses to start on a dirty tree.
2. **A test must catch it.** `run_tests` is how the agent proves its own fix. A bug no
   test sees means it is guessing, and so are you.
3. **It must live under `editable_paths`** — currently `poc/sample_site/` only. Anything
   else is refused by design.

---

## The loop

**1. Make sure the container is up**

```powershell
cd D:\ai-dlc-project\poc; docker compose up -d
```

**2. Plant the bug and push it**

Edit something under `poc\sample_site\`, then:

```powershell
cd D:\ai-dlc-project; git commit -am "Bug: <what you broke>"; git push
```

If no existing test catches it, add one in the same commit. You write the test; the agent
cannot — `tests/` is protected, which is exactly what stops it passing by cheating.

**3. Pull it into the agent's clone — the step that is easy to forget**

```powershell
git -C D:\ai-dlc-project\poc\workspace\agentic-ai-sdlc pull
```

**4. Check the baseline you expect the agent to report**

```powershell
cd D:\ai-dlc-project\poc\workspace\agentic-ai-sdlc; python -m unittest discover -s poc/sample_site/tests -q
```

Note the failure count. If the agent reports a different one, it is reading something else.

**5. Give it the task — the symptom, not the fix**

```powershell
cd D:\ai-dlc-project\poc; python call_agent.py "The about page has a malformed closing tag. Find it and fix it."
```

Saying "change `</htmll>` to `</html>`" tests find-and-replace, not diagnosis.

**6. Approve, then verify independently**

```powershell
python call_agent.py --approve s-xxxxxxxx
```

```powershell
gh pr diff <n> --repo dipesharma29/agentic-ai-sdlc --name-only
```

---

## What good looks like

- Baseline failure count matches step 4.
- Final run: your bug's failure gone.
- The diff touches only the files the task needed.
- No file under `tests/` changed.
- A human approved before anything was pushed.

**Read the diff, not the summary.** The agent's own report is model output; the diff is
what happened. On the 25 Nov run the report was accurate but the scope was wider than
asked — only the diff showed that.

---

## Reset between runs

The clone is left **on the agent's branch**, and its `main` is behind:

```powershell
cd D:\ai-dlc-project\poc\workspace\agentic-ai-sdlc; git checkout main; git pull
```

```powershell
cd D:\ai-dlc-project; git pull
```

`create_branch` does `git checkout main` with **no fetch**, so without this the next run
branches from a stale base.

To throw a planted bug away instead of letting the agent fix it:

```powershell
cd D:\ai-dlc-project; git revert --no-edit <bug-commit>; git push
```

---

## When it says the problem is not there

It is probably right, about a different copy of the file. The reply names the checkout and
commit it searched. Compare that against:

```powershell
git -C D:\ai-dlc-project\poc\workspace\agentic-ai-sdlc rev-parse --short HEAD
```

A mismatch means step 3 was missed.

---

## Gotchas

- **Three agents appear in the list.** ADK scans recursively and finds the copies inside
  the clone. Always pick the plain `fix_agent`.
- **Your `main` is red while a planted bug sits on it.** Fine mid-experiment; do not leave
  it there before a demo.
- **The sandbox is green again.** Both originally planted issues have now been fixed, so a
  new run needs a bug you plant yourself.
