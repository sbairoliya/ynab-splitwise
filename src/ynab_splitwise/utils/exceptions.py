"""Custom exceptions for YNAB-Splitwise integration."""

from typing import Optional


class YnabSplitwiseError(Exception):
    """Base exception for YNAB-Splitwise integration."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


class AuthenticationError(YnabSplitwiseError):
    """Raised when authentication fails."""

    pass


class ConfigurationError(YnabSplitwiseError):
    """Raised when configuration is invalid or missing."""

    pass


class SplitwiseAPIError(YnabSplitwiseError):
    """Raised when Splitwise API operations fail."""

    pass


class YnabAPIError(YnabSplitwiseError):
    """Raised when YNAB API operations fail."""

    pass


class DataProcessingError(YnabSplitwiseError):
    """Raised when data processing fails."""

    pass


class DuplicateTransactionError(YnabSplitwiseError):
    """Raised when duplicate transaction detection fails."""

    pass


class AccountNotFoundError(YnabSplitwiseError):
    """Raised when specified YNAB account cannot be found."""

    pass
