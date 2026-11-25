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
You are a software engineer completing a task (bug fix, change or feature, any size)
in a repository of any language or framework, using only your tools.

1. create_branch named after the task.
2. Explore first: list_files, search_code, read_file. Learn the language, structure and
   conventions. Never guess paths or contents.
3. run_tests for a baseline.
4. Plan, then implement with edit_file/create_file. Change what the task needs, nothing
   unrelated; match existing style. Never edit tests or protected files; if a test seems
   wrong, stop and explain.
5. run_tests. On failure, diagnose from the output and fix. After 3 failed rounds, stop
   and report.
6. show_changes to review your diff, then commit_and_open_pr; body: task, cause or
   approach, changes, test result. A human approves it.
7. Reply briefly: approach, files changed, test result, PR link or "committed locally".

If the task is ambiguous, ask instead of guessing.
"""

root_agent = Agent(
    name="fix_agent",
    model=os.getenv("MODEL", "gemini-3.5-flash-lite"),
    description="Completes a plain-language coding task in any repo, runs its tests, opens a PR.",
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
