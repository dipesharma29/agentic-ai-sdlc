"""Send a task to the Fix Agent over ADK's REST API and print what it did.

Usage:
  python call_agent.py "The About link on the home page is broken. Fix it."
  python call_agent.py --approve <session_id>   # approve the pending commit/PR
  python call_agent.py --reject  <session_id>   # reject it
"""

import json
import sys
import urllib.request
import uuid

BASE = "http://localhost:8000"
APP, USER = "fix_agent", "dipesh"


def post(path, body):
    req = urllib.request.Request(BASE + path, method="POST", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read() or b"null")


def run(session_id, parts):
    events = post("/run", {"app_name": APP, "user_id": USER, "session_id": session_id,
                           "new_message": {"role": "user", "parts": parts}})
    pending = None
    for e in events:
        for p in (e.get("content") or {}).get("parts", []):
            if p.get("functionCall"):
                fc = p["functionCall"]
                if fc["name"] == "adk_request_confirmation":
                    pending = fc
                    print(f"\n>>> APPROVAL NEEDED: {json.dumps(fc['args'].get('originalFunctionCall', {}).get('args', {}))[:600]}")
                else:
                    print(f"[tool call] {fc['name']}({json.dumps(fc.get('args', {}))[:200]})")
            elif p.get("functionResponse"):
                resp = json.dumps(p["functionResponse"].get("response", {}))
                print(f"   -> {p['functionResponse']['name']}: {resp[:200]}")
            elif p.get("text"):
                print(f"\n[agent] {p['text']}")
    return pending


def main():
    if sys.argv[1] in ("--approve", "--reject"):
        session_id = sys.argv[2]
        # Find the pending confirmation call id from the session history.
        with urllib.request.urlopen(f"{BASE}/apps/{APP}/users/{USER}/sessions/{session_id}") as r:
            session = json.loads(r.read())
        call = None
        for e in session.get("events", []):
            for p in (e.get("content") or {}).get("parts", []):
                if (p.get("functionCall") or {}).get("name") == "adk_request_confirmation":
                    call = p["functionCall"]
        if not call:
            sys.exit("No pending approval found in that session.")
        confirmed = sys.argv[1] == "--approve"
        run(session_id, [{"functionResponse": {"id": call["id"], "name": "adk_request_confirmation",
                                               "response": {"confirmed": confirmed}}}])
        return

    session_id = "s-" + uuid.uuid4().hex[:8]
    post(f"/apps/{APP}/users/{USER}/sessions/{session_id}", {})
    print(f"session: {session_id}\ntask: {sys.argv[1]}\n")
    if run(session_id, [{"text": sys.argv[1]}]):
        print(f"\nApprove:  python call_agent.py --approve {session_id}")
        print(f"Reject:   python call_agent.py --reject {session_id}")


if __name__ == "__main__":
    main()
