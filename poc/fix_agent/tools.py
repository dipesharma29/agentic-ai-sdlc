"""Tools for the Fix Agent. Language-agnostic: everything repo-specific comes from
the target repo's .agent.json (test command, protected paths, optional editable paths).

Guardrails are enforced here in code, not in the prompt:
- every path must stay inside the target repo;
- if editable_paths is set, only files under those folders can be changed;
- protected paths (tests, config, .git) can't be edited;
- edits are exact find-and-replace (must match exactly once);
- the only command that can run is the repo's test_command (no shell);
- git work happens only on branches named agent/*; nothing is ever merged.
"""

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

# Default matches poc/docker-compose.yml and fix_agent/.env.example. A wrong path here
# surfaces as "Target repo has no .agent.json" on the first tool call.
REPO = Path(os.getenv("TARGET_REPO", "/app/poc/workspace/agentic-ai-sdlc")).resolve()
SKIP_DIRS = {".git", "node_modules", "target", "build", "dist", "__pycache__", ".venv"}
MAX_READ_LINES = 400
TEST_TIMEOUT_SECONDS = int(os.getenv("TEST_TIMEOUT_SECONDS", "300"))
BRANCH_PREFIX = "agent/"


# ---------- helpers ----------

def _config() -> dict:
    path = REPO / ".agent.json"
    if not path.exists():
        raise FileNotFoundError("Target repo has no .agent.json (test_command, protected_paths)")
    return json.loads(path.read_text(encoding="utf-8"))


def _inside_repo(relative_path: str) -> Path:
    target = (REPO / relative_path).resolve()
    if target != REPO and REPO not in target.parents:
        raise PermissionError(f"'{relative_path}' is outside the repository")
    return target


def _check_editable(relative_path: str) -> Path:
    target = _inside_repo(relative_path)
    rel = target.relative_to(REPO).as_posix()
    config = _config()
    editable = [p.rstrip("/") for p in config.get("editable_paths", [])]  # optional allow-list
    if editable and not any(e in ("", ".") or rel == e or rel.startswith(e + "/") for e in editable):
        raise PermissionError(f"'{rel}' is outside the editable paths {editable}")
    for protected in config.get("protected_paths", []) + [".git/"]:
        p = protected.rstrip("/")
        if rel == p or rel.startswith(p + "/"):
            raise PermissionError(f"'{rel}' is protected and can't be changed by the agent")
    return target


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, timeout=120)


def _current_branch() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def _repo_id() -> str:
    """Which checkout, at which commit. Attached to every empty or missing result.

    The agent works on a clone at TARGET_REPO, not on the human's working tree.
    When someone edits their own copy and the agent says "no such problem", both
    are telling the truth about different files. Saying where we looked turns a
    confusing disagreement into an obvious one.
    """
    head = _git("rev-parse", "--short", "HEAD").stdout.strip() or "unknown"
    return f"{REPO} @ {head} ({_current_branch() or 'unknown'})"


# ---------- read ----------

def list_files(sub_path: str = "") -> dict:
    """List files in the target repository (optionally under a sub-folder).

    Args:
        sub_path: folder inside the repo; empty for the whole repo.
    """
    try:
        root = _inside_repo(sub_path)
    except PermissionError as e:
        return {"status": "error", "message": str(e)}
    files = sorted(p.relative_to(REPO).as_posix() for p in root.rglob("*")
                   if p.is_file() and not (SKIP_DIRS & set(p.relative_to(REPO).parts)))
    return {"status": "success", "count": len(files), "files": files[:500]}


def search_code(keywords: str, max_results: int = 30) -> dict:
    """Find lines containing any of the keywords (case-insensitive). Lines matching more keywords rank first.

    Args:
        keywords: space-separated words, e.g. 'about href nav'.
        max_results: maximum lines to return.
    """
    words = [w.lower() for w in keywords.split() if w]
    if not words:
        return {"status": "error", "message": "Give at least one keyword"}
    scored = []
    for rel in list_files()["files"]:
        try:
            lines = (REPO / rel).read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable file
        for n, line in enumerate(lines, 1):
            hits = sum(w in line.lower() for w in words)
            if hits:
                scored.append((hits, f"{rel}:{n}: {line.strip()[:200]}"))
    scored.sort(key=lambda s: -s[0])
    if not scored:
        return {"status": "success", "matches": [], "truncated": False,
                "searched": _repo_id(),
                "note": "No match in the target repo. If a human says it is there, they may "
                        "be looking at a different checkout, or the change is uncommitted."}
    return {"status": "success", "matches": [m for _, m in scored[:max_results]],
            "truncated": len(scored) > max_results}


def read_file(path: str) -> dict:
    """Read a text file from the target repository (first 400 lines, with line numbers).

    Args:
        path: repo-relative path.
    """
    try:
        target = _inside_repo(path)
        lines = target.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {"status": "error", "message": f"No such file in {_repo_id()}: {path}"}
    except (PermissionError, UnicodeDecodeError, IsADirectoryError) as e:
        return {"status": "error", "message": str(e)}
    numbered = "\n".join(f"{i:4}| {l}" for i, l in enumerate(lines[:MAX_READ_LINES], 1))
    return {"status": "success", "path": path, "total_lines": len(lines), "content": numbered}


# ---------- change ----------

def edit_file(path: str, old_text: str, new_text: str) -> dict:
    """Replace one exact piece of text in a file. old_text must appear exactly once
    (include enough surrounding text to make it unique). Do not include line-number prefixes.

    Args:
        path: repo-relative path.
        old_text: exact existing text to replace.
        new_text: replacement text.
    """
    try:
        target = _check_editable(path)
        content = target.read_text(encoding="utf-8")
    except (PermissionError, FileNotFoundError, UnicodeDecodeError) as e:
        return {"status": "error", "message": str(e)}
    if not _current_branch().startswith(BRANCH_PREFIX):
        return {"status": "error", "message": "Create an agent/ branch with create_branch before editing"}
    count = content.count(old_text)
    if count != 1:
        return {"status": "error", "message": f"old_text found {count} times; it must match exactly once"}
    target.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
    return {"status": "success", "path": path}


def create_file(path: str, content: str) -> dict:
    """Create a NEW text file in the target repository. Refuses to overwrite an existing file.

    Args:
        path: repo-relative path of the new file.
        content: full file content.
    """
    try:
        target = _check_editable(path)
    except (PermissionError, FileNotFoundError) as e:
        return {"status": "error", "message": str(e)}
    if target.exists():
        return {"status": "error", "message": "File already exists; use edit_file instead"}
    if not _current_branch().startswith(BRANCH_PREFIX):
        return {"status": "error", "message": "Create an agent/ branch with create_branch before editing"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"status": "success", "path": path}


def run_tests() -> dict:
    """Run the repository's own test command (from .agent.json). No other commands can be run."""
    try:
        command = _config()["test_command"]
    except (FileNotFoundError, KeyError) as e:
        return {"status": "error", "message": f"No test_command configured: {e}"}
    try:
        result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=TEST_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": f"Tests timed out after {TEST_TIMEOUT_SECONDS}s"}
    output = (result.stdout + result.stderr)[-4000:]
    return {"status": "passed" if result.returncode == 0 else "failed", "exit_code": result.returncode, "output": output}


# ---------- git / PR ----------

def create_branch(name: str) -> dict:
    """Create and switch to a new working branch from the base branch. The name gets the 'agent/' prefix.

    Args:
        name: short kebab-case name, e.g. 'fix-about-link'.
    """
    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    slug = re.sub(r"^agent-", "", slug)[:50]
    if not slug:
        return {"status": "error", "message": "Invalid branch name"}
    branch = BRANCH_PREFIX + slug
    base = os.getenv("BASE_BRANCH", "main")
    if _git("status", "--porcelain").stdout.strip():
        return {"status": "error", "message": "Working tree has uncommitted changes; a human must clean it up first"}
    _git("checkout", base)
    r = _git("checkout", "-b", branch)
    if r.returncode != 0:
        return {"status": "error", "message": r.stderr.strip()}
    return {"status": "success", "branch": branch, "base": base}


def show_changes() -> dict:
    """Show the diff of all uncommitted changes the agent has made."""
    return {"status": "success", "branch": _current_branch(), "diff": _git("diff").stdout[-6000:]}


def commit_and_open_pr(title: str, body: str) -> dict:
    """Commit all changes on the current agent/ branch, push it, and open a pull request.
    Only call this after run_tests passed. A human reviews and merges the PR; you never merge.

    Args:
        title: short PR title.
        body: PR description: the task, root cause, what changed, test result.
    """
    branch = _current_branch()
    if not branch.startswith(BRANCH_PREFIX):
        return {"status": "error", "message": "Not on an agent/ branch"}
    if not _git("status", "--porcelain").stdout.strip():
        return {"status": "error", "message": "No changes to commit"}
    _git("add", "-A")
    c = _git("commit", "-m", title)
    if c.returncode != 0:
        return {"status": "error", "message": c.stderr.strip()}

    repo_slug, token = os.getenv("GITHUB_REPO", ""), os.getenv("GITHUB_TOKEN", "")
    if not (repo_slug and token):
        return {"status": "success", "committed_locally": True, "branch": branch,
                "note": "GITHUB_REPO / GITHUB_TOKEN not set, so nothing was pushed and no PR was opened."}

    push_url = f"https://x-access-token:{token}@github.com/{repo_slug}.git"
    p = _git("push", push_url, f"{branch}:{branch}")
    if p.returncode != 0:
        return {"status": "error", "message": p.stderr.replace(token, "***").strip()}

    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo_slug}/pulls", method="POST",
        data=json.dumps({"title": title, "body": body, "head": branch,
                         "base": os.getenv("BASE_BRANCH", "main")}).encode(),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            pr = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        # The branch is already pushed, so say so: the work is not lost and a
        # human can open the PR by hand. Common causes: a PR already exists for
        # this branch, or the token lacks pull-request write access.
        detail = e.read().decode("utf-8", "replace")[:300].replace(token, "***")
        return {"status": "error", "pushed": True, "branch": branch,
                "message": f"Pushed, but GitHub refused the pull request ({e.code}): {detail}"}
    except urllib.error.URLError as e:
        return {"status": "error", "pushed": True, "branch": branch,
                "message": f"Pushed, but could not reach GitHub: {str(e.reason)[:200]}"}
    return {"status": "success", "branch": branch, "pr_url": pr.get("html_url")}
