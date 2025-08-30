import os
import unittest
import uuid

from github import GithubException
from zdownloadmanager.core.github_adapter import GitHubAdapter


class GitHubAdapterTests(unittest.TestCase):
    def test_get_repo_info(self) -> None:
        token = os.getenv("GITHUB_TOKEN")
        adapter = GitHubAdapter(token)
        info = adapter.get_repo_info("octocat/Hello-World")
        self.assertEqual(info["full_name"], "octocat/Hello-World")

    def test_list_open_issues(self) -> None:
        token = os.getenv("GITHUB_TOKEN")
        adapter = GitHubAdapter(token)
        issues = adapter.list_open_issues("octocat/Hello-World", limit=2)
        self.assertIsInstance(issues, list)
        for issue in issues:
            self.assertIn("number", issue)
            self.assertIn("title", issue)

    def test_list_open_pull_requests(self) -> None:
        token = os.getenv("GITHUB_TOKEN")
        adapter = GitHubAdapter(token)
        pulls = adapter.list_open_pull_requests("python/cpython", limit=2)
        self.assertIsInstance(pulls, list)
        self.assertGreater(len(pulls), 0)
        for pr in pulls:
            self.assertIn("number", pr)
            self.assertIn("title", pr)

    def test_list_languages(self) -> None:
        token = os.getenv("GITHUB_TOKEN")
        adapter = GitHubAdapter(token)
        languages = adapter.list_languages("python/cpython")
        self.assertIn("Python", languages)
        self.assertIsInstance(languages["Python"], int)

    def test_create_branch_and_commit_files(self) -> None:
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_TEST_REPO")
        if not token or not repo:
            self.skipTest("Requires GITHUB_TOKEN and GITHUB_TEST_REPO")
        adapter = GitHubAdapter(token)
        branch = f"test-{uuid.uuid4().hex[:8]}"
        adapter.create_branch(repo, branch)
        file_path = f"test_{uuid.uuid4().hex}.txt"
        adapter.commit_files(repo, {file_path: "hello"}, "test commit", branch)
        content = adapter._gh.get_repo(repo).get_contents(file_path, ref=branch)
        self.assertEqual(content.decoded_content.decode(), "hello")
        adapter.delete_branch(repo, branch)
        with self.assertRaises(GithubException):
            adapter._gh.get_repo(repo).get_branch(branch)
