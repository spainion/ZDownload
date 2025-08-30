import os
import unittest

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
