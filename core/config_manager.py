"""Configuration manager for sBitx Branch Manager"""

import json
from pathlib import Path
from typing import List, Optional
from models.repository import Repository


class ConfigError(Exception):
    """Configuration-related errors"""
    pass


class ConfigManager:
    """Manages application configuration and repository list"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config manager

        Args:
            config_dir: Directory to store configuration files.
                       Defaults to {project_root}/config
        """
        if config_dir is None:
            # Default to config/ in project root
            project_root = Path(__file__).parent.parent
            config_dir = project_root / 'config'

        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / 'repositories.json'
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> dict:
        """
        Load configuration from JSON file

        Returns:
            Configuration dictionary

        Raises:
            ConfigError: If config file is corrupted
        """
        if not self.config_file.exists():
            return self._create_default_config()

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            # Ensure default_repositories key exists
            if 'default_repositories' not in config:
                config['default_repositories'] = ['https://github.com/drexjj/sbitx.git']
                self.save_config(config)

            return config
        except json.JSONDecodeError as e:
            # Backup corrupted config
            backup_file = self.config_file.with_suffix('.json.backup')
            if self.config_file.exists():
                self.config_file.rename(backup_file)

            raise ConfigError(
                f"Config file is corrupted: {e}\n"
                f"Backup saved to: {backup_file}\n"
                "Creating new config..."
            )
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}")

    def _create_default_config(self) -> dict:
        """Create default configuration"""
        from models.repository import Repository

        # Add default repository (drexjj/sbitx)
        default_repo = Repository.create_new('drexjj/sbitx')

        config = {
            'repositories': [default_repo.to_dict()] if default_repo else [],
            'default_repositories': ['https://github.com/drexjj/sbitx.git'],
            'last_used_repo': '',
            'last_used_branch': ''
        }
        self.save_config(config)
        return config

    def save_config(self, config: dict):
        """
        Save configuration to JSON file

        Args:
            config: Configuration dictionary to save

        Raises:
            ConfigError: If save fails
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}")

    def load_repositories(self) -> List[Repository]:
        """
        Load repository list from config file

        Returns:
            List of Repository objects
        """
        config = self.load_config()
        repos = []
        for repo_data in config.get('repositories', []):
            try:
                repos.append(Repository.from_dict(repo_data))
            except Exception:
                # Skip invalid repository entries
                continue
        return repos

    def save_repositories(self, repositories: List[Repository]):
        """
        Save repository list to config file

        Args:
            repositories: List of Repository objects to save
        """
        config = self.load_config()
        config['repositories'] = [repo.to_dict() for repo in repositories]
        self.save_config(config)

    def add_repository(self, repository: Repository) -> bool:
        """
        Add a repository to the config

        Args:
            repository: Repository to add

        Returns:
            True if added, False if already exists
        """
        repos = self.load_repositories()

        # Check if repository already exists
        for repo in repos:
            if repo.url == repository.url:
                return False

        repos.append(repository)
        self.save_repositories(repos)
        return True

    def is_default_repository(self, url: str) -> bool:
        """
        Check if a repository is a default (non-removable) repository

        Args:
            url: Repository URL to check

        Returns:
            True if it's a default repository
        """
        config = self.load_config()
        default_repos = config.get('default_repositories', [])
        return url in default_repos

    def remove_repository(self, url: str) -> bool:
        """
        Remove a repository from the config (cannot remove default repos)

        Args:
            url: URL of repository to remove

        Returns:
            True if removed, False if not found or is a default repo
        """
        # Check if it's a default repository
        if self.is_default_repository(url):
            return False

        repos = self.load_repositories()
        initial_count = len(repos)

        repos = [repo for repo in repos if repo.url != url]

        if len(repos) < initial_count:
            self.save_repositories(repos)
            return True
        return False

    def get_last_used(self) -> tuple[str, str]:
        """
        Get last used repository and branch

        Returns:
            Tuple of (repo_url, branch_name)
        """
        config = self.load_config()
        return (
            config.get('last_used_repo', ''),
            config.get('last_used_branch', '')
        )

    def set_last_used(self, repo_url: str, branch_name: str):
        """
        Save last used repository and branch

        Args:
            repo_url: Repository URL
            branch_name: Branch name
        """
        config = self.load_config()
        config['last_used_repo'] = repo_url
        config['last_used_branch'] = branch_name
        self.save_config(config)
