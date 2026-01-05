"""Git operations manager for sBitx Branch Manager"""

import subprocess
from pathlib import Path
from typing import List, Optional
from enum import Enum
from dataclasses import dataclass


class DirectoryStatus(Enum):
    """Status of target directory"""
    DOES_NOT_EXIST = "does_not_exist"
    GIT_REPO = "git_repo"
    NON_GIT = "non_git"


@dataclass
class CommandResult:
    """Result of a git command execution"""
    success: bool
    returncode: int


class GitError(Exception):
    """Git operation errors"""
    pass


class GitManager:
    """Manages all git operations for repository checkout and branch management"""

    @staticmethod
    def check_directory_status(path: str) -> DirectoryStatus:
        """
        Check the status of target directory

        Args:
            path: Path to check

        Returns:
            DirectoryStatus enum value
        """
        dir_path = Path(path)

        if not dir_path.exists():
            return DirectoryStatus.DOES_NOT_EXIST

        # Check if it's a git repository
        result = subprocess.run(
            ['git', 'rev-parse', '--is-inside-work-tree'],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return DirectoryStatus.GIT_REPO
        else:
            return DirectoryStatus.NON_GIT

    @staticmethod
    def fetch_branches(repo_url: str) -> List[str]:
        """
        Fetch branch list from remote repository without cloning

        Args:
            repo_url: Repository URL

        Returns:
            List of branch names

        Raises:
            GitError: If fetch fails
        """
        try:
            result = subprocess.run(
                ['git', 'ls-remote', '--heads', repo_url],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise GitError(
                    f"Failed to fetch branches from {repo_url}\n"
                    f"Error: {result.stderr}\n"
                    "Check your network connection and repository URL."
                )

            branches = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Format: "hash\trefs/heads/branch_name"
                    parts = line.split('\t')
                    if len(parts) == 2:
                        ref = parts[1]
                        branch_name = ref.replace('refs/heads/', '')
                        branches.append(branch_name)

            return sorted(branches)

        except subprocess.TimeoutExpired:
            raise GitError(
                f"Timeout while fetching branches from {repo_url}\n"
                "Check your network connection."
            )
        except Exception as e:
            raise GitError(f"Failed to fetch branches: {e}")

    @staticmethod
    def clone_repository(repo_url: str, target_path: str) -> CommandResult:
        """
        Clone repository to target path

        Args:
            repo_url: Repository URL to clone
            target_path: Path where to clone

        Returns:
            CommandResult with operation details

        Raises:
            GitError: If clone fails
        """
        try:
            print(f"\n=== Cloning {repo_url} to {target_path} ===")
            result = subprocess.run(
                ['git', 'clone', repo_url, target_path],
                timeout=300  # 5 minutes
            )

            if result.returncode != 0:
                raise GitError(f"Failed to clone repository (exit code: {result.returncode})")

            print("=== Clone completed ===\n")
            return CommandResult(
                success=True,
                returncode=result.returncode
            )

        except subprocess.TimeoutExpired:
            raise GitError(
                f"Timeout while cloning {repo_url}\n"
                "The repository might be too large or network is slow."
            )
        except Exception as e:
            raise GitError(f"Failed to clone repository: {e}")

    @staticmethod
    def change_remote(repo_url: str, target_path: str) -> CommandResult:
        """
        Change the remote origin URL of existing repository

        Args:
            repo_url: New repository URL
            target_path: Path to existing git repository

        Returns:
            CommandResult with operation details

        Raises:
            GitError: If operation fails
        """
        try:
            # Change remote URL
            print(f"\n=== Changing remote to {repo_url} ===")
            result = subprocess.run(
                ['git', 'remote', 'set-url', 'origin', repo_url],
                cwd=target_path,
                timeout=10
            )

            if result.returncode != 0:
                raise GitError(f"Failed to change remote URL (exit code: {result.returncode})")

            # Prune old remote refs to avoid conflicts
            print("=== Pruning old remote references ===")
            prune_result = subprocess.run(
                ['git', 'remote', 'prune', 'origin'],
                cwd=target_path,
                timeout=30
            )

            # Fetch from new remote with prune to clean up stale refs
            print("=== Fetching from new remote ===")
            fetch_result = subprocess.run(
                ['git', 'fetch', 'origin', '--prune'],
                cwd=target_path,
                timeout=300  # 5 minutes
            )

            if fetch_result.returncode != 0:
                raise GitError(f"Failed to fetch from new remote (exit code: {fetch_result.returncode})")

            print("=== Remote changed successfully ===\n")
            return CommandResult(
                success=True,
                returncode=0
            )

        except subprocess.TimeoutExpired:
            raise GitError("Timeout while fetching from new remote")
        except Exception as e:
            raise GitError(f"Failed to change remote: {e}")

    @staticmethod
    def checkout_branch(branch: str, target_path: str) -> CommandResult:
        """
        Checkout a specific branch, creating local branch to track remote

        Args:
            branch: Branch name to checkout
            target_path: Path to git repository

        Returns:
            CommandResult with operation details

        Raises:
            GitError: If checkout fails
        """
        try:
            # Use checkout -B to create/reset branch to match remote
            print(f"\n=== Checking out branch '{branch}' ===")
            result = subprocess.run(
                ['git', 'checkout', '-B', branch, f'origin/{branch}'],
                cwd=target_path,
                timeout=60
            )

            if result.returncode != 0:
                raise GitError(
                    f"Failed to checkout branch '{branch}' (exit code: {result.returncode})\n"
                    "Make sure the branch exists on the remote."
                )

            print(f"=== Branch '{branch}' checked out successfully ===\n")
            return CommandResult(
                success=True,
                returncode=result.returncode
            )

        except subprocess.TimeoutExpired:
            raise GitError(f"Timeout while checking out branch '{branch}'")
        except Exception as e:
            raise GitError(f"Failed to checkout branch: {e}")

    @staticmethod
    def get_current_branch(target_path: str) -> Optional[str]:
        """
        Get the current branch name

        Args:
            target_path: Path to git repository

        Returns:
            Branch name or None if not in a git repo
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=target_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None

        except Exception:
            return None

    @staticmethod
    def get_current_remote(target_path: str) -> Optional[str]:
        """
        Get the current remote origin URL (normalized)

        Args:
            target_path: Path to git repository

        Returns:
            Normalized remote URL or None if not in a git repo
        """
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=target_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                url = result.stdout.strip()
                # Normalize URL to match our repository format
                from models.repository import Repository
                normalized = Repository.validate_and_normalize_url(url)
                return normalized if normalized else url
            return None

        except Exception:
            return None

    @staticmethod
    def update_submodules(target_path: str) -> CommandResult:
        """
        Update git submodules (required for sBitx build)

        Args:
            target_path: Path to git repository

        Returns:
            CommandResult with operation details

        Raises:
            GitError: If submodule update fails
        """
        try:
            print("\n=== Updating submodules ===")
            result = subprocess.run(
                ['git', 'submodule', 'update', '--init', '--recursive'],
                cwd=target_path,
                timeout=300  # 5 minutes
            )

            if result.returncode != 0:
                raise GitError(f"Failed to update submodules (exit code: {result.returncode})")

            print("=== Submodules updated successfully ===\n")
            return CommandResult(
                success=True,
                returncode=result.returncode
            )

        except subprocess.TimeoutExpired:
            raise GitError("Timeout while updating submodules")
        except Exception as e:
            raise GitError(f"Failed to update submodules: {e}")
