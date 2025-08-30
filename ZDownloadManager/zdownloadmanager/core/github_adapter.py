"""GitHub API integration helpers."""
from __future__ import annotations

from typing import Optional, Dict, Any, List

from github import Github, InputGitTreeElement, GithubException


class GitHubAdapter:
    """Simple wrapper around the GitHub API.

    Parameters
    ----------
    token:
        Personal access token with the required scopes. If ``None`` the
        adapter performs unauthenticated requests which are heavily rate
        limited.
    """

    def __init__(self, token: Optional[str] = None) -> None:
        self._gh = Github(login_or_token=token)

    def get_repo_info(self, full_name: str) -> Dict[str, Optional[str]]:
        """Return basic information about a repository."""
        repo = self._gh.get_repo(full_name)
        return {"full_name": repo.full_name, "description": repo.description}

    def commit_file(
        self,
        repo_full_name: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> None:
        """Create or update a file in ``repo_full_name``.

        If the file exists it is updated, otherwise it is created.
        """
        repo = self._gh.get_repo(repo_full_name)
        try:
            existing = repo.get_contents(path, ref=branch)
            repo.update_file(path, message, content, existing.sha, branch=branch)
        except Exception:
            repo.create_file(path, message, content, branch=branch)

    def commit_files(
        self,
        repo_full_name: str,
        files: Dict[str, str],
        message: str,
        branch: str = "main",
    ) -> None:
        """Commit multiple ``files`` to ``repo_full_name`` in a single commit."""
        repo = self._gh.get_repo(repo_full_name)
        ref = repo.get_git_ref(f"heads/{branch}")
        base_tree = repo.get_git_tree(ref.object.sha)
        elements = []
        for path, content in files.items():
            blob = repo.create_git_blob(content, "utf-8")
            elements.append(InputGitTreeElement(path, "100644", "blob", blob.sha))
        tree = repo.create_git_tree(elements, base_tree)
        parent = repo.get_git_commit(ref.object.sha)
        commit = repo.create_git_commit(message, tree, [parent])
        ref.edit(commit.sha)

    def create_branch(
        self, repo_full_name: str, branch: str, from_branch: str = "main"
    ) -> None:
        """Create ``branch`` in ``repo_full_name`` from ``from_branch``."""
        repo = self._gh.get_repo(repo_full_name)
        source = repo.get_branch(from_branch)
        repo.create_git_ref(ref=f"refs/heads/{branch}", sha=source.commit.sha)

    def delete_branch(self, repo_full_name: str, branch: str) -> None:
        """Delete ``branch`` from ``repo_full_name`` if it exists."""
        repo = self._gh.get_repo(repo_full_name)
        try:
            ref = repo.get_git_ref(f"heads/{branch}")
            ref.delete()
        except GithubException:
            pass

    def create_pull_request(
        self,
        repo_full_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> str:
        """Open a pull request and return its URL."""
        repo = self._gh.get_repo(repo_full_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        return pr.html_url

    def list_open_issues(self, repo_full_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return up to ``limit`` open issues for ``repo_full_name``."""
        repo = self._gh.get_repo(repo_full_name)
        issues = repo.get_issues(state="open")[:limit]
        return [{"number": issue.number, "title": issue.title} for issue in issues]

    def list_open_pull_requests(
        self, repo_full_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return up to ``limit`` open pull requests for ``repo_full_name``."""
        repo = self._gh.get_repo(repo_full_name)
        pulls = repo.get_pulls(state="open")[:limit]
        return [{"number": pr.number, "title": pr.title} for pr in pulls]

    def list_languages(self, repo_full_name: str) -> Dict[str, int]:
        """Return the languages used in ``repo_full_name``.

        The mapping keys are language names with byte counts as values.
        """
        repo = self._gh.get_repo(repo_full_name)
        return repo.get_languages()
