"""Transaction processing and transformation logic."""

from datetime import datetime
from typing import Any, Dict, List

from dateutil.parser import parse as parse_date

from ..utils.exceptions import DataProcessingError
from ..utils.logger import LoggerMixin
from .duplicate_detector import DuplicateDetector


class TransactionProcessor(LoggerMixin):
    """Processes Splitwise expenses and converts them to YNAB transactions."""

    def __init__(self) -> None:
        """Initialize transaction processor."""
        self.duplicate_detector = DuplicateDetector()
        self.logger.info("Transaction processor initialized")

    def process_expenses_for_user(
        self, expenses: List[Dict[str, Any]], user_id: int
    ) -> List[Dict[str, Any]]:
        """Process Splitwise expenses and convert to YNAB transactions for a specific user.

        Args:
            expenses: List of Splitwise expense objects
            user_id: Splitwise user ID to process expenses for

        Returns:
            List of YNAB transaction dictionaries

        Raises:
            DataProcessingError: If processing fails
        """
        transactions = []

        self.logger.info(f"Processing {len(expenses)} expenses for user {user_id}")

        for expense in expenses:
            try:
                transaction = self._convert_expense_to_transaction(expense, user_id)
                if transaction:  # Only add if user has a share in this expense
                    transactions.append(transaction)
            except Exception as e:
                expense_id = expense.get("id", "unknown")
                error_msg = f"Failed to process expense {expense_id}: {str(e)}"
                self.logger.error(error_msg)
                raise DataProcessingError(error_msg, details=str(e))

        self.logger.info(f"Successfully processed {len(transactions)} transactions")
        return transactions

    def _convert_expense_to_transaction(
        self, expense: Dict[str, Any], user_id: int
    ) -> Dict[str, Any] | None:
        """Convert a single Splitwise expense to a YNAB transaction.

        Args:
            expense: Splitwise expense object
            user_id: Splitwise user ID

        Returns:
            YNAB transaction dictionary or None if user has no share

        Raises:
            DataProcessingError: If conversion fails
        """
        try:
            # Extract basic expense information
            expense_id = str(expense.get("id"))
            description = expense.get("description", "Unknown Expense")
            expense_date = self._parse_expense_date(expense.get("date"))
            currency_code = expense.get("currency_code", "USD")

            # Find user's share in this expense
            user_share = self._get_user_share(expense, user_id)

            if user_share is None:
                # User is not involved in this expense
                self.logger.debug(
                    f"User {user_id} not involved in expense {expense_id}"
                )
                return None

            # Calculate the amount for YNAB
            amount_milliunits = self._calculate_ynab_amount(user_share)

            if amount_milliunits == 0:
                # No net amount for this user
                self.logger.debug(
                    f"User {user_id} has no net amount for expense {expense_id}"
                )
                return None

            # Generate memo with detailed information
            memo = self._generate_memo(expense, user_share)

            # Generate import ID for duplicate detection
            import_id = self.duplicate_detector.generate_import_id(expense_id)

            transaction = {
                "amount": amount_milliunits,
                "payee_name": description,
                "memo": memo,
                "date": expense_date,
                "import_id": import_id,
                "splitwise_expense_id": expense_id,
                "currency_code": currency_code,
            }

            self.logger.debug(
                f"Converted expense {expense_id} to transaction: "
                f"{description} - ${amount_milliunits/1000:.2f}"
            )

            return transaction

        except Exception as e:
            expense_id = expense.get("id", "unknown")
            raise DataProcessingError(
                f"Failed to convert expense {expense_id}", details=str(e)
            )

    def _parse_expense_date(self, date_str: str) -> datetime:
        """Parse expense date string to datetime object.

        Args:
            date_str: Date string from Splitwise

        Returns:
            Parsed datetime object

        Raises:
            DataProcessingError: If date parsing fails
        """
        if not date_str:
            raise DataProcessingError("Missing expense date")

        try:
            return parse_date(date_str)
        except Exception as e:
            raise DataProcessingError(
                f"Invalid date format: {date_str}", details=str(e)
            )

    def _get_user_share(
        self, expense: Dict[str, Any], user_id: int
    ) -> Dict[str, float] | None:
        """Get user's share information from expense.

        Args:
            expense: Splitwise expense object
            user_id: User ID to find share for

        Returns:
            Dictionary with paid, owed, and net amounts, or None if user not involved
        """
        users = expense.get("users", [])

        for user_data in users:
            if user_data.get("user_id") == user_id:
                paid_share = float(user_data.get("paid_share", "0"))
                owed_share = float(user_data.get("owed_share", "0"))

                return {
                    "paid": paid_share,
                    "owed": owed_share,
                    "net": paid_share - owed_share,
                }

        return None

    def _calculate_ynab_amount(self, user_share: Dict[str, float]) -> int:
        """Calculate the YNAB transaction amount in milliunits.

        Based on user requirements:
        - Import user's owed share (negative for money owed)
        - Import money user gets back (positive for money received)

        Args:
            user_share: Dictionary with paid, owed, and net amounts

        Returns:
            Amount in milliunits (negative for owed, positive for received)
        """
        net_amount = user_share["net"]

        if net_amount > 0:
            # User gets money back (positive amount)
            return int(round(net_amount * 1000))
        elif net_amount < 0:
            # User owes money (negative amount)
            return int(round(net_amount * 1000))  # Already negative
        else:
            # No net amount
            return 0

    def _generate_memo(
        self, expense: Dict[str, Any], user_share: Dict[str, float]
    ) -> str:
        """Generate detailed memo for the transaction.

        Args:
            expense: Splitwise expense object
            user_share: User's share information

        Returns:
            Formatted memo string
        """
        memo_parts = []

        # Add paid and owed information
        paid = user_share["paid"]
        owed = user_share["owed"]
        memo_parts.append(f"Paid: ${paid:.2f}, Owed: ${owed:.2f}")

        # Add users involved in the expense
        users = expense.get("users", [])
        user_names = []
        for user_data in users:
            user = user_data.get("user", {})
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            if first_name or last_name:
                name = f"{first_name} {last_name}".strip()
                user_names.append(name)

        if user_names:
            memo_parts.append(f"Users: {', '.join(user_names)}")

        # Add expense details if available
        details = expense.get("details")
        if details and details.strip():
            memo_parts.append(f"Notes: {details.strip()}")

        # Add Splitwise expense ID for reference
        expense_id = expense.get("id")
        if expense_id:
            memo_parts.append(f"Splitwise ID: {expense_id}")

        return " | ".join(memo_parts)

    def filter_duplicates(
        self, transactions: List[Dict[str, Any]], existing_import_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter out duplicate transactions.

        Args:
            transactions: List of new transactions
            existing_import_ids: List of import IDs that already exist in YNAB

        Returns:
            List of transactions that are not duplicates
        """
        return self.duplicate_detector.filter_existing_transactions(
            transactions, existing_import_ids
        )

    def validate_transactions(self, transactions: List[Dict[str, Any]]) -> None:
        """Validate transactions before sending to YNAB.

        Args:
            transactions: List of transactions to validate

        Raises:
            DataProcessingError: If validation fails
        """
        try:
            self.duplicate_detector.validate_import_ids(transactions)

            for i, txn in enumerate(transactions):
                # Validate required fields
                required_fields = ["amount", "payee_name", "memo", "date", "import_id"]
                for field in required_fields:
                    if field not in txn or txn[field] is None:
                        raise DataProcessingError(
                            f"Transaction {i} missing required field: {field}",
                            details=f"Transaction: {txn}",
                        )

                # Validate data types and ranges
                if not isinstance(txn["amount"], int):
                    raise DataProcessingError(
                        f"Transaction {i} amount must be integer (milliunits)",
                        details=f"Got: {type(txn['amount'])}",
                    )

                if (
                    not isinstance(txn["payee_name"], str)
                    or not txn["payee_name"].strip()
                ):
                    raise DataProcessingError(
                        f"Transaction {i} payee_name must be non-empty string",
                        details=f"Got: {txn['payee_name']}",
                    )

                if not isinstance(txn["date"], datetime):
                    raise DataProcessingError(
                        f"Transaction {i} date must be datetime object",
                        details=f"Got: {type(txn['date'])}",
                    )

            self.logger.info(f"Validated {len(transactions)} transactions successfully")

        except Exception as e:
            if isinstance(e, DataProcessingError):
                raise
            raise DataProcessingError("Transaction validation failed", details=str(e))
