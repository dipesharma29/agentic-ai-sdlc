"""Guardrail tests for the Fix Agent's tools.

Every test here tries to do something the agent must not be able to do, and
asserts that the tool refuses. A passing suite is the evidence that a refactor
has not quietly removed a limit; reading the code is not evidence.

The tools read ``TARGET_REPO`` once, at import time, so each test builds a
throwaway git repository and loads the module fresh against it.

``tools.py`` is loaded straight from its path rather than through the
``fix_agent`` package, whose ``__init__`` pulls in ADK. That keeps the suite
runnable with nothing installed, and makes the "standard library only" rule in
AGENTS.md something these tests enforce rather than something a comment claims.

Run from the repository root::

    python -m unittest discover -s poc/tests -q
"""

import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

TOOLS_PATH = Path(__file__).resolve().parents[1] / "fix_agent" / "tools.py"


def load_tools():
    """Import poc/fix_agent/tools.py fresh, so it re-reads TARGET_REPO."""
    spec = importlib.util.spec_from_file_location("fix_agent_tools_under_test", TOOLS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

AGENT_CONFIG = """{
  "test_command": ["python", "-c", "open('ran.txt', 'w').write('yes')"],
  "editable_paths": ["src/"],
  "protected_paths": [".agent.json", "src/tests/"]
}
"""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


class GuardrailTest(unittest.TestCase):
    """Base: a disposable repo, with the tools module pointed at it."""

    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp(prefix="fix-agent-guardrail-")).resolve()
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)

        (self.repo / "src" / "tests").mkdir(parents=True)
        (self.repo / ".agent.json").write_text(AGENT_CONFIG, encoding="utf-8")
        (self.repo / "src" / "page.html").write_text(
            "<p>hello</p>\n<p>unique line</p>\n<p>twice</p>\n<p>twice</p>\n", encoding="utf-8")
        (self.repo / "src" / "tests" / "test_page.py").write_text("# the required behaviour\n", encoding="utf-8")
        (self.repo / "README.md").write_text("# outside the editable paths\n", encoding="utf-8")

        git(self.repo, "init", "--quiet", "-b", "main")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "user.name", "Guardrail Test")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", "initial")

        self._saved_env = {k: os.environ.get(k) for k in ("TARGET_REPO", "BASE_BRANCH", "GITHUB_REPO", "GITHUB_TOKEN")}
        self.addCleanup(self._restore_env)
        os.environ["TARGET_REPO"] = str(self.repo)
        os.environ["BASE_BRANCH"] = "main"
        os.environ.pop("GITHUB_REPO", None)
        os.environ.pop("GITHUB_TOKEN", None)

        self.tools = load_tools()

    def _restore_env(self) -> None:
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def on_agent_branch(self) -> None:
        """Put the repo in the only state where edits are allowed."""
        result = self.tools.create_branch("fix-something")
        self.assertEqual(result["status"], "success", result)

    def assertRefused(self, result: dict, because: str) -> None:
        self.assertEqual(result.get("status"), "error", f"expected a refusal, got {result}")
        self.assertIn(because, result.get("message", "").lower(), result)


class PathContainment(GuardrailTest):
    """Nothing outside the target repository, by any spelling of the path."""

    def test_read_refuses_parent_traversal(self):
        self.assertRefused(self.tools.read_file("../secret.txt"), "outside the repository")

    def test_read_refuses_traversal_buried_mid_path(self):
        self.assertRefused(self.tools.read_file("src/../../secret.txt"), "outside the repository")

    def test_read_refuses_absolute_path(self):
        outside = self.repo.parent / "secret.txt"
        self.assertRefused(self.tools.read_file(str(outside)), "outside the repository")

    def test_list_files_refuses_traversal(self):
        self.assertRefused(self.tools.list_files(".."), "outside the repository")

    def test_edit_refuses_traversal(self):
        self.on_agent_branch()
        outside = self.repo.parent / "victim.txt"
        outside.write_text("untouched\n", encoding="utf-8")
        self.addCleanup(outside.unlink, True)
        self.assertRefused(self.tools.edit_file("../victim.txt", "untouched", "owned"), "outside the repository")
        self.assertEqual(outside.read_text(encoding="utf-8"), "untouched\n")

    def test_create_file_refuses_traversal(self):
        self.on_agent_branch()
        self.assertRefused(self.tools.create_file("../planted.txt", "x"), "outside the repository")
        self.assertFalse((self.repo.parent / "planted.txt").exists())


class EditablePaths(GuardrailTest):
    """When editable_paths is set, it is an allow-list and nothing else counts."""

    def test_edit_outside_editable_paths_is_refused(self):
        self.on_agent_branch()
        self.assertRefused(self.tools.edit_file("README.md", "outside", "changed"), "editable paths")

    def test_create_outside_editable_paths_is_refused(self):
        self.on_agent_branch()
        self.assertRefused(self.tools.create_file("newfile.txt", "x"), "editable paths")

    def test_edit_inside_editable_paths_is_allowed(self):
        self.on_agent_branch()
        result = self.tools.edit_file("src/page.html", "unique line", "fixed line")
        self.assertEqual(result["status"], "success", result)
        self.assertIn("fixed line", (self.repo / "src" / "page.html").read_text(encoding="utf-8"))

    def test_a_prefix_match_is_not_a_path_match(self):
        """'src-other/' must not pass because it starts with 'src'."""
        self.on_agent_branch()
        (self.repo / "src-other").mkdir()
        self.assertRefused(self.tools.create_file("src-other/x.txt", "x"), "editable paths")


class ProtectedPaths(GuardrailTest):
    """Tests state the required behaviour; config decides what may run."""

    def drop_the_allow_list(self) -> None:
        """Remove editable_paths, leaving protected_paths as the only defence.

        Most target repos will not set an allow-list, so protected_paths has to
        hold on its own. With both set, editable_paths refuses first and a
        broken protected_paths would never show.
        """
        (self.repo / ".agent.json").write_text(
            '{"test_command": ["python", "-c", "pass"],'
            ' "protected_paths": [".agent.json", "src/tests/"]}', encoding="utf-8")

    def test_cannot_edit_the_tests_that_judge_it(self):
        self.on_agent_branch()
        self.assertRefused(
            self.tools.edit_file("src/tests/test_page.py", "# the required behaviour", "# deleted"), "protected")

    def test_cannot_create_a_file_inside_tests(self):
        self.on_agent_branch()
        self.assertRefused(self.tools.create_file("src/tests/test_extra.py", "pass"), "protected")

    def test_cannot_rewrite_its_own_rules(self):
        """.agent.json names the command that gets executed, so it must protect itself."""
        self.on_agent_branch()
        self.drop_the_allow_list()
        self.assertRefused(self.tools.edit_file(".agent.json", "python", "curl"), "protected")

    def test_git_internals_are_protected_without_being_listed(self):
        self.on_agent_branch()
        self.drop_the_allow_list()
        self.assertRefused(self.tools.edit_file(".git/config", "[core]", "[evil]"), "protected")

    def test_protected_paths_still_refuse_without_an_allow_list(self):
        self.on_agent_branch()
        self.drop_the_allow_list()
        self.assertRefused(
            self.tools.edit_file("src/tests/test_page.py", "# the required behaviour", "# gone"), "protected")
        self.assertIn("required behaviour",
                      (self.repo / "src" / "tests" / "test_page.py").read_text(encoding="utf-8"))

    def test_a_sibling_of_a_protected_folder_is_still_editable(self):
        """The check must not treat 'src/tests-notes' as being inside 'src/tests/'."""
        self.on_agent_branch()
        self.drop_the_allow_list()
        result = self.tools.create_file("src/tests-notes.md", "notes\n")
        self.assertEqual(result["status"], "success", result)


class BranchRequirement(GuardrailTest):
    """Work starts with create_branch, or it does not start."""

    def test_edit_on_the_base_branch_is_refused(self):
        self.assertRefused(self.tools.edit_file("src/page.html", "unique line", "changed"), "create an agent/ branch")

    def test_create_file_on_the_base_branch_is_refused(self):
        self.assertRefused(self.tools.create_file("src/new.html", "x"), "create an agent/ branch")

    def test_branch_names_are_forced_under_the_agent_prefix(self):
        result = self.tools.create_branch("../../main")
        self.assertEqual(result["status"], "success", result)
        self.assertTrue(result["branch"].startswith("agent/"), result)

    def test_branch_name_cannot_double_the_prefix(self):
        result = self.tools.create_branch("agent-fix-thing")
        self.assertEqual(result["branch"], "agent/fix-thing", result)

    def test_branching_from_a_dirty_tree_is_refused(self):
        (self.repo / "src" / "page.html").write_text("uncommitted human work\n", encoding="utf-8")
        self.assertRefused(self.tools.create_branch("fix-something"), "uncommitted changes")

    def test_commit_and_open_pr_refuses_off_an_agent_branch(self):
        self.assertRefused(self.tools.commit_and_open_pr("title", "body"), "not on an agent/ branch")


class ExactMatchEdits(GuardrailTest):
    """A replacement that is not unique is a guess, so it is refused."""

    def test_ambiguous_text_is_refused(self):
        self.on_agent_branch()
        result = self.tools.edit_file("src/page.html", "<p>twice</p>", "<p>once</p>")
        self.assertRefused(result, "found 2 times")

    def test_absent_text_is_refused(self):
        self.on_agent_branch()
        self.assertRefused(self.tools.edit_file("src/page.html", "not in the file", "x"), "found 0 times")

    def test_a_refused_edit_leaves_the_file_untouched(self):
        self.on_agent_branch()
        before = (self.repo / "src" / "page.html").read_text(encoding="utf-8")
        self.tools.edit_file("src/page.html", "<p>twice</p>", "<p>once</p>")
        self.assertEqual((self.repo / "src" / "page.html").read_text(encoding="utf-8"), before)

    def test_create_file_refuses_to_overwrite(self):
        self.on_agent_branch()
        self.assertRefused(self.tools.create_file("src/page.html", "clobbered"), "already exists")
        self.assertIn("hello", (self.repo / "src" / "page.html").read_text(encoding="utf-8"))


class CommandExecution(GuardrailTest):
    """run_tests is the only way to execute anything, and it runs one fixed command."""

    def test_run_tests_runs_the_configured_command(self):
        result = self.tools.run_tests()
        self.assertEqual(result["status"], "passed", result)
        self.assertTrue((self.repo / "ran.txt").exists())

    def test_run_tests_reports_failure_rather_than_raising(self):
        (self.repo / ".agent.json").write_text(
            '{"test_command": ["python", "-c", "raise SystemExit(1)"], "protected_paths": []}', encoding="utf-8")
        self.assertEqual(self.tools.run_tests()["status"], "failed")

    def test_missing_test_command_is_reported_not_raised(self):
        (self.repo / ".agent.json").write_text('{"protected_paths": []}', encoding="utf-8")
        self.assertRefused(self.tools.run_tests(), "no test_command")

    def test_the_test_command_is_not_run_through_a_shell(self):
        """A shell would make ';' a command separator. subprocess without shell=True does not."""
        marker = self.repo / "pwned.txt"
        (self.repo / ".agent.json").write_text(
            '{"test_command": ["python", "-c", "pass; import pathlib", "&&", "touch pwned.txt"],'
            ' "protected_paths": []}', encoding="utf-8")
        self.tools.run_tests()
        self.assertFalse(marker.exists())


class ToolsNeverRaise(GuardrailTest):
    """Every tool returns a dict. An exception ends the agent's turn with nothing to correct."""

    def test_missing_file_is_an_error_dict_naming_the_checkout(self):
        result = self.tools.read_file("src/nope.html")
        self.assertEqual(result["status"], "error")
        self.assertIn(str(self.repo), result["message"])

    def test_empty_search_is_an_error_dict(self):
        self.assertEqual(self.tools.search_code("   ")["status"], "error")

    def test_search_with_no_hits_says_where_it_looked(self):
        result = self.tools.search_code("zzz-nothing-matches-this")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["matches"], [])
        self.assertIn(str(self.repo), result["searched"])

    def test_editing_a_missing_file_is_an_error_dict(self):
        self.on_agent_branch()
        self.assertEqual(self.tools.edit_file("src/nope.html", "a", "b")["status"], "error")


if __name__ == "__main__":
    unittest.main()
