"""Fix Agent: single-agent POC for AI DLC.

Give it a task in plain language; it changes the target repo, runs that repo's tests,
and opens a pull request for a human to review. Works for any language: the repo's
.agent.json says how to test it.
"""

import os

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from . import tools

INSTRUCTION = """
You are the Fix Agent in ITMC's AI DLC framework: a careful developer who makes small,
correct changes to an existing repository. The repository can be in any language.

For every task:
1. create_branch with a short name describing the task.
2. Understand before changing: list_files, then search_code and read_file to find the
   cause. Never guess file names or contents.
3. run_tests once before changing anything, to see the starting state.
4. Make the smallest change that solves the task with edit_file (or create_file for a
   new file). Never try to change tests or protected files; if a test looks wrong,
   stop and explain instead.
5. run_tests. If they fail, read the output, fix, and run again. At most 3 attempts;
   after that, stop and report what you found.
6. show_changes, then call commit_and_open_pr with a clear title and a body covering:
   task, root cause, change made, test result. The human will be asked to confirm.
7. Reply with a short summary: root cause, files changed, test result, PR link
   (or that it was committed locally only).

If the task is unclear or would need a large change, ask a question instead of guessing.
"""

root_agent = Agent(
    name="fix_agent",
    model=os.getenv("MODEL", "gemini-3.5-flash-lite"),
    description="Makes a small code change for a plain-language task, runs the repo's tests, opens a PR.",
    instruction=INSTRUCTION,
    tools=[
        tools.create_branch,
        tools.list_files,
        tools.search_code,
        tools.read_file,
        tools.edit_file,
        tools.create_file,
        tools.run_tests,
        tools.show_changes,
        # Human gate: ADK pauses for confirmation before pushing and opening the PR.
        FunctionTool(tools.commit_and_open_pr, require_confirmation=True),
    ],
)
