"""Configuration and authentication management."""

import os

from ..utils.exceptions import AuthenticationError, ConfigurationError
from ..utils.logger import LoggerMixin


class Config(LoggerMixin):
    """Configuration manager for YNAB-Splitwise integration."""

    def __init__(self) -> None:
        """Initialize configuration from environment variables."""
        self.splitwise_api_key = self._get_env_var("SPLITWISE_API_KEY")
        self.ynab_access_token = self._get_env_var("YNAB_ACCESS_TOKEN")
        self.ynab_account_name = os.getenv("YNAB_ACCOUNT_NAME", "Splitwise (Wallet)")
        self.ynab_api_url = os.getenv("YNAB_API_URL", "https://api.ynab.com/v1")
        self.splitwise_api_url = os.getenv(
            "SPLITWISE_API_URL", "https://secure.splitwise.com/api/v3.0"
        )

        self.logger.info("Configuration loaded successfully")

    def _get_env_var(self, var_name: str) -> str:
        """Get required environment variable or raise error.

        Args:
            var_name: Name of environment variable

        Returns:
            Value of environment variable

        Raises:
            ConfigurationError: If environment variable is not set
        """
        value = os.getenv(var_name)
        if not value:
            self.logger.error(f"Missing required environment variable: {var_name}")
            raise ConfigurationError(
                f"Missing required environment variable: {var_name}",
                details=f"Please set {var_name} in your environment",
            )
        return value

    def validate(self) -> None:
        """Validate configuration settings.

        Raises:
            AuthenticationError: If API credentials are invalid
            ConfigurationError: If configuration is invalid
        """
        self.logger.info("Validating configuration...")

        # Validate API key format (basic check)
        if not self.splitwise_api_key or len(self.splitwise_api_key) < 10:
            raise AuthenticationError(
                "Invalid Splitwise API key format",
                details="API key should be a long alphanumeric string",
            )

        # Validate YNAB token format (basic check)
        if not self.ynab_access_token or len(self.ynab_access_token) < 10:
            raise AuthenticationError(
                "Invalid YNAB access token format",
                details="Access token should be a long alphanumeric string",
            )

        # Validate account name
        if not self.ynab_account_name or not self.ynab_account_name.strip():
            raise ConfigurationError(
                "Invalid YNAB account name", details="Account name cannot be empty"
            )

        self.logger.info("Configuration validation completed successfully")

    def get_splitwise_headers(self) -> dict[str, str]:
        """Get headers for Splitwise API requests.

        Returns:
            Dictionary of headers including authorization
        """
        return {
            "Authorization": f"Bearer {self.splitwise_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_ynab_config(self) -> dict[str, str]:
        """Get configuration for YNAB API client.

        Returns:
            Dictionary with YNAB configuration
        """
        return {"access_token": self.ynab_access_token, "host": self.ynab_api_url}
