"""Tools the Requirements Agent can call.

Version 1 is deliberately simple and runs locally:
- the transcript is read from a file,
- the Java repo is searched with plain text matching (RAG replaces this in a later step),
- Jira is reached with its REST API using credentials from .env.
If no Jira credentials are set, approved stories are saved as Markdown files instead.
"""

import base64
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

PROTOTYPE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = PROTOTYPE_DIR.parent
INPUTS_DIR = PROTOTYPE_DIR / "inputs"
OUTPUT_DIR = PROTOTYPE_DIR / "output" / "stories"
REPO_DIR = Path(os.getenv("REPO_PATH", PROJECT_DIR / "workspace" / "spring-petclinic")).resolve()

CODE_SUFFIXES = {".java", ".html", ".sql", ".properties", ".yml", ".yaml", ".xml", ".md"}
SKIP_DIRS = {".git", "target", "build", "node_modules", ".mvn", ".gradle"}


# ---------- Requirement sources ----------

def read_meeting_transcript() -> dict:
    """Read the meeting transcript (WebVTT) and return it as 'Speaker: text' lines.

    Returns:
        dict with 'status' and 'transcript' (plain text, one spoken line per row).
    """
    path = INPUTS_DIR / "meeting_transcript.vtt"
    if not path.exists():
        return {"status": "error", "message": f"Transcript not found at {path}"}
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if (not stripped or stripped == "WEBVTT" or "-->" in stripped
                or re.fullmatch(r"[0-9a-f-]{36}(/\d+-\d+)?", stripped)):
            continue
        lines.append(re.sub(r"<v ([^>]*)>", r"\1: ", stripped).replace("</v>", ""))
    return {"status": "success", "transcript": "\n".join(lines)}


# ---------- Existing code (brownfield context) ----------

def _safe_path(relative_path: str) -> Path:
    """Resolve a path inside the repo and refuse anything outside it."""
    target = (REPO_DIR / relative_path).resolve()
    if REPO_DIR not in target.parents and target != REPO_DIR:
        raise ValueError("Path is outside the repository")
    return target


def list_repo_files(sub_path: str = "") -> dict:
    """List source files in the Java repository, optionally under a sub-folder.

    Args:
        sub_path: folder inside the repo, e.g. 'src/main/java'. Empty means the whole repo.
    Returns:
        dict with 'status' and 'files' (repo-relative paths).
    """
    if not REPO_DIR.exists():
        return {"status": "error", "message": f"Repository not found at {REPO_DIR}"}
    root = _safe_path(sub_path)
    files = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in CODE_SUFFIXES and not (SKIP_DIRS & set(p.parts)):
            files.append(p.relative_to(REPO_DIR).as_posix())
    return {"status": "success", "count": len(files), "files": sorted(files)[:400]}


def search_code(keywords: str, max_results: int = 30) -> dict:
    """Search the Java repository for lines containing any of the given keywords (case-insensitive).

    Args:
        keywords: space-separated words, e.g. 'owner email telephone'.
        max_results: maximum matching lines to return.
    Returns:
        dict with 'status' and 'matches' as 'path:line: text'.
    """
    words = [w.lower() for w in keywords.split() if w.strip()]
    if not words:
        return {"status": "error", "message": "Give at least one keyword"}
    listing = list_repo_files()
    if listing["status"] != "success":
        return listing
    scored = []
    for rel in listing["files"]:
        try:
            text = (REPO_DIR / rel).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        is_source = rel.startswith("src/")
        for n, line in enumerate(text.splitlines(), 1):
            hits = sum(w in line.lower() for w in words)
            if hits:
                # More keywords on one line rank higher; application source beats docs.
                scored.append((hits + (0.5 if is_source else 0), f"{rel}:{n}: {line.strip()[:160]}"))
    scored.sort(key=lambda s: -s[0])
    matches = [m for _, m in scored[:max_results]]
    return {"status": "success", "matches": matches, "truncated": len(scored) > max_results}


def read_code_file(path: str) -> dict:
    """Read one file from the Java repository.

    Args:
        path: repo-relative path, as returned by list_repo_files or search_code.
    Returns:
        dict with 'status' and 'content' (first 400 lines).
    """
    try:
        target = _safe_path(path)
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    if not target.is_file():
        return {"status": "error", "message": f"No such file: {path}"}
    lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
    return {"status": "success", "path": path, "content": "\n".join(lines[:400]), "total_lines": len(lines)}


# ---------- Jira ----------

def _jira_config():
    base = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    email = os.getenv("JIRA_EMAIL", "")
    token = os.getenv("JIRA_API_TOKEN", "")
    return (base, email, token) if base and email and token else None


def _jira_request(method: str, path: str, body: dict | None = None) -> dict:
    base, email, token = _jira_config()
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    req = urllib.request.Request(
        base + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Basic {auth}", "Accept": "application/json",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read() or b"{}")


def search_jira_history(text: str) -> dict:
    """Search past Jira tickets in the prototype project for related work.

    Args:
        text: words to search for, e.g. 'owner telephone'.
    Returns:
        dict with 'status' and 'issues' (key, summary, labels).
    """
    if not _jira_config():
        return {"status": "skipped", "message": "Jira credentials not set in .env; no history available."}
    project = os.getenv("JIRA_PROJECT_KEY", "KAN")
    jql = f'project = {project} AND labels = "ai-sdlc-prototype" AND text ~ "{text}" ORDER BY created DESC'
    data = _jira_request("GET", "/rest/api/3/search/jql?" + urllib.parse.urlencode(
        {"jql": jql, "fields": "summary,labels,description", "maxResults": 10}))
    issues = [{"key": i["key"], "summary": i["fields"]["summary"], "labels": i["fields"].get("labels", [])}
              for i in data.get("issues", [])]
    return {"status": "success", "issues": issues}


def _to_adf(markdown: str) -> dict:
    """Very small Markdown-to-Jira-document conversion: one paragraph per line."""
    content = [{"type": "paragraph", "content": [{"type": "text", "text": line}]}
               for line in markdown.splitlines() if line.strip()]
    return {"type": "doc", "version": 1, "content": content}


def save_user_story(summary: str, story_markdown: str) -> dict:
    """Save an APPROVED user story. Only call after the human has approved the draft.

    Creates a Story in Jira under the prototype epic if Jira credentials are set,
    otherwise writes a Markdown file to prototype/output/stories.

    Args:
        summary: one-line story title.
        story_markdown: full story text (user story, acceptance criteria, code areas, open questions).
    Returns:
        dict with 'status' and where the story was saved.
    """
    if _jira_config():
        body = {"fields": {
            "project": {"key": os.getenv("JIRA_PROJECT_KEY", "KAN")},
            "issuetype": {"name": "Story"},
            "summary": summary,
            "description": _to_adf(story_markdown),
            "labels": ["ai-sdlc-prototype", "agent-drafted"],
        }}
        parent = os.getenv("JIRA_PARENT_EPIC", "KAN-4")
        if parent:
            body["fields"]["parent"] = {"key": parent}
        created = _jira_request("POST", "/rest/api/3/issue", body)
        return {"status": "success", "saved_to": "jira", "key": created.get("key")}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", summary.lower()).strip("-")[:60]
    path = OUTPUT_DIR / f"{datetime.now():%Y%m%d-%H%M%S}-{slug}.md"
    path.write_text(f"# {summary}\n\n{story_markdown}\n", encoding="utf-8")
    return {"status": "success", "saved_to": "file", "path": str(path)}
