#!/usr/bin/env python3
"""Command line utilities for GitHub automation."""
from __future__ import annotations

import argparse
import os
import sys

from zdownloadmanager.core.github_adapter import GitHubAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub helper tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    commit = sub.add_parser("commit-file", help="Create or update a file")
    commit.add_argument("repo", help="owner/repo")
    commit.add_argument("path", help="Path within the repository")
    commit.add_argument("message", help="Commit message")
    commit.add_argument("content", help="File content")
    commit.add_argument("--branch", default="main")

    commit_multi = sub.add_parser("commit-files", help="Commit multiple files")
    commit_multi.add_argument("repo", help="owner/repo")
    commit_multi.add_argument("message", help="Commit message")
    commit_multi.add_argument("files", nargs="+", help="file=content pairs")
    commit_multi.add_argument("--branch", default="main")

    branch = sub.add_parser("create-branch", help="Create a branch")
    branch.add_argument("repo", help="owner/repo")
    branch.add_argument("name", help="New branch name")
    branch.add_argument("--from-branch", default="main")

    del_branch = sub.add_parser("delete-branch", help="Delete a branch")
    del_branch.add_argument("repo", help="owner/repo")
    del_branch.add_argument("name", help="Branch name to delete")

    pr = sub.add_parser("create-pr", help="Open a pull request")
    pr.add_argument("repo", help="owner/repo")
    pr.add_argument("title")
    pr.add_argument("head", help="User:branch to merge from")
    pr.add_argument("--base", default="main")
    pr.add_argument("--body", default="")

    issues = sub.add_parser("list-issues", help="List open issues")
    issues.add_argument("repo", help="owner/repo")
    issues.add_argument("--limit", type=int, default=10)

    pulls = sub.add_parser("list-prs", help="List open pull requests")
    pulls.add_argument("repo", help="owner/repo")
    pulls.add_argument("--limit", type=int, default=10)

    langs = sub.add_parser("list-languages", help="List repository languages")
    langs.add_argument("repo", help="owner/repo")

    args = parser.parse_args()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(1)

    adapter = GitHubAdapter(token)

    if args.cmd == "commit-file":
        adapter.commit_file(args.repo, args.path, args.content, args.message, branch=args.branch)
    elif args.cmd == "commit-files":
        files = dict(f.split("=", 1) for f in args.files)
        adapter.commit_files(args.repo, files, args.message, branch=args.branch)
    elif args.cmd == "create-branch":
        adapter.create_branch(args.repo, args.name, from_branch=args.from_branch)
    elif args.cmd == "delete-branch":
        adapter.delete_branch(args.repo, args.name)
    elif args.cmd == "create-pr":
        url = adapter.create_pull_request(args.repo, args.title, args.body, args.head, base=args.base)
        print(url)
    elif args.cmd == "list-issues":
        issues = adapter.list_open_issues(args.repo, limit=args.limit)
        for issue in issues:
            print(f"#{issue['number']} {issue['title']}")
    elif args.cmd == "list-prs":
        prs = adapter.list_open_pull_requests(args.repo, limit=args.limit)
        for pr in prs:
            print(f"#{pr['number']} {pr['title']}")
    elif args.cmd == "list-languages":
        languages = adapter.list_languages(args.repo)
        for name, count in languages.items():
            print(f"{name}: {count}")


if __name__ == "__main__":
    main()
