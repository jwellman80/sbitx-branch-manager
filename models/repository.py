"""Repository data model for sBitx Branch Manager"""

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Optional


@dataclass
class Repository:
    """Represents a GitHub repository"""
    url: str
    display_name: str
    added_date: str

    def get_short_name(self) -> str:
        """
        Extract owner/repo from URL

        Returns:
            Short name in format "owner/repo"
        """
        # Extract from HTTPS URL: https://github.com/owner/repo.git
        https_match = re.search(r'github\.com/([^/]+/[^/]+?)(\.git)?$', self.url)
        if https_match:
            return https_match.group(1)

        # Extract from SSH URL: git@github.com:owner/repo.git
        ssh_match = re.search(r'github\.com:([^/]+/[^/]+?)(\.git)?$', self.url)
        if ssh_match:
            return ssh_match.group(1)

        # Fallback to display_name
        return self.display_name

    @staticmethod
    def validate_and_normalize_url(url: str) -> Optional[str]:
        """
        Validate and normalize GitHub repository URL

        Args:
            url: Repository URL in various formats

        Returns:
            Normalized URL with .git suffix, or None if invalid
        """
        # Remove whitespace
        url = url.strip()

        # HTTPS pattern: https://github.com/user/repo or https://github.com/user/repo.git
        https_pattern = r'^https://github\.com/([\w-]+/[\w-]+)(\.git)?$'
        https_match = re.match(https_pattern, url)
        if https_match:
            base = https_match.group(1)
            return f'https://github.com/{base}.git'

        # SSH pattern: git@github.com:user/repo or git@github.com:user/repo.git
        ssh_pattern = r'^git@github\.com:([\w-]+/[\w-]+)(\.git)?$'
        ssh_match = re.match(ssh_pattern, url)
        if ssh_match:
            return url if url.endswith('.git') else url + '.git'

        # Short pattern: user/repo or github.com/user/repo
        short_pattern = r'^(github\.com/)?([\w-]+/[\w-]+)$'
        short_match = re.match(short_pattern, url)
        if short_match:
            user_repo = short_match.group(2)
            return f'https://github.com/{user_repo}.git'

        # Invalid URL
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'url': self.url,
            'display_name': self.display_name,
            'added_date': self.added_date
        }

    @staticmethod
    def from_dict(data: dict) -> 'Repository':
        """Create Repository from dictionary"""
        return Repository(
            url=data['url'],
            display_name=data['display_name'],
            added_date=data['added_date']
        )

    @staticmethod
    def create_new(url: str) -> Optional['Repository']:
        """
        Create a new Repository with validated URL

        Args:
            url: Repository URL to validate and normalize

        Returns:
            Repository instance or None if URL is invalid
        """
        normalized_url = Repository.validate_and_normalize_url(url)
        if not normalized_url:
            return None

        # Extract display name from URL
        display_name = re.search(r'github\.com[/:]([\w-]+/[\w-]+)', normalized_url)
        if display_name:
            display_name = display_name.group(1)
        else:
            display_name = normalized_url

        return Repository(
            url=normalized_url,
            display_name=display_name,
            added_date=datetime.now().isoformat()
        )
