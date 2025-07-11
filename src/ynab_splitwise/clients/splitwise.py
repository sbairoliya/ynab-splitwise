"""Splitwise API client."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from ..auth.config import Config
from ..utils.exceptions import SplitwiseAPIError
from ..utils.logger import LoggerMixin


class SplitwiseClient(LoggerMixin):
    """Client for interacting with the Splitwise API."""

    def __init__(self, config: Config) -> None:
        """Initialize Splitwise client.

        Args:
            config: Configuration object with API credentials
        """
        self.config = config
        self.base_url = config.splitwise_api_url
        self.headers = config.get_splitwise_headers()
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        self.logger.info("Splitwise client initialized")

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the Splitwise API.

        Args:
            endpoint: API endpoint (e.g., '/get_expenses')
            params: Query parameters

        Returns:
            JSON response from API

        Raises:
            SplitwiseAPIError: If API request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            self.logger.debug(f"Making request to {url} with params: {params}")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Check for Splitwise API errors
            if "errors" in data and data["errors"]:
                error_msg = f"Splitwise API error: {data['errors']}"
                self.logger.error(error_msg)
                raise SplitwiseAPIError(error_msg, details=str(data["errors"]))

            self.logger.debug(f"Successfully received response from {url}")
            return data

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            self.logger.error(error_msg)
            raise SplitwiseAPIError(error_msg, details=str(e))
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            self.logger.error(error_msg)
            raise SplitwiseAPIError(error_msg, details=str(e))
        except ValueError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            self.logger.error(error_msg)
            raise SplitwiseAPIError(error_msg, details=str(e))

    def get_current_user(self) -> Dict[str, Any]:
        """Get current user information.

        Returns:
            User information from Splitwise

        Raises:
            SplitwiseAPIError: If API request fails
        """
        self.logger.info("Fetching current user information")
        data = self._make_request("/get_current_user")

        if "user" not in data:
            raise SplitwiseAPIError("Invalid response: missing user data")

        user = data["user"]
        self.logger.info(
            f"Current user: {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('email', '')})"
        )
        return user

    def get_expenses(
        self,
        dated_after: Optional[datetime] = None,
        dated_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get expenses for the current user.

        Args:
            dated_after: Only include expenses after this date
            dated_before: Only include expenses before this date
            limit: Maximum number of expenses to return (default: 50)
            offset: Number of expenses to skip (default: 0)

        Returns:
            List of expense objects

        Raises:
            SplitwiseAPIError: If API request fails
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}

        if dated_after:
            params["dated_after"] = dated_after.isoformat()
        if dated_before:
            params["dated_before"] = dated_before.isoformat()

        self.logger.info(f"Fetching expenses with params: {params}")
        data = self._make_request("/get_expenses", params)

        if "expenses" not in data:
            raise SplitwiseAPIError("Invalid response: missing expenses data")

        expenses = data["expenses"]
        self.logger.info(f"Retrieved {len(expenses)} expenses")
        return expenses

    def get_all_expenses_since(self, start_date: datetime) -> List[Dict[str, Any]]:
        """Get all expenses since a given date using pagination.

        Args:
            start_date: Date to start fetching expenses from

        Returns:
            List of all expense objects since start_date

        Raises:
            SplitwiseAPIError: If API request fails
        """
        all_expenses = []
        offset = 0
        limit = 100  # Use larger batch size for efficiency

        self.logger.info(f"Fetching all expenses since {start_date.isoformat()}")

        while True:
            expenses = self.get_expenses(
                dated_after=start_date, limit=limit, offset=offset
            )

            if not expenses:
                break

            all_expenses.extend(expenses)
            offset += limit

            # If we got fewer than the limit, we've reached the end
            if len(expenses) < limit:
                break

        self.logger.info(
            f"Retrieved total of {len(all_expenses)} expenses since {start_date.isoformat()}"
        )
        return all_expenses

    def get_user_share_for_expense(
        self, expense: Dict[str, Any], user_id: int
    ) -> Dict[str, float]:
        """Calculate user's share for a specific expense.

        Args:
            expense: Expense object from Splitwise API
            user_id: ID of the user to calculate share for

        Returns:
            Dictionary with 'paid', 'owed', and 'net' amounts
        """
        paid_share = 0.0
        owed_share = 0.0

        # Find user in the expense users list
        for user_data in expense.get("users", []):
            if user_data.get("user_id") == user_id:
                paid_share = float(user_data.get("paid_share", "0"))
                owed_share = float(user_data.get("owed_share", "0"))
                break

        net_amount = paid_share - owed_share

        return {"paid": paid_share, "owed": owed_share, "net": net_amount}
