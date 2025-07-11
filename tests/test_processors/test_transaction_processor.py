"""Tests for transaction processor."""

from datetime import datetime

import pytest

from src.ynab_splitwise.processors.transaction_processor import TransactionProcessor
from src.ynab_splitwise.utils.exceptions import DataProcessingError
from tests.fixtures.sample_data import (
    SAMPLE_EXPENSE,
    SAMPLE_EXPENSE_GETS_BACK,
    SAMPLE_EXPENSE_NOT_INVOLVED,
    SAMPLE_EXPENSE_OWED,
    SAMPLE_USER,
)


class TestTransactionProcessor:
    """Test transaction processing logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = TransactionProcessor()
        self.user_id = SAMPLE_USER["id"]

    def test_process_expenses_for_user_success(self):
        """Test successful expense processing."""
        expenses = [SAMPLE_EXPENSE, SAMPLE_EXPENSE_OWED, SAMPLE_EXPENSE_GETS_BACK]

        transactions = self.processor.process_expenses_for_user(expenses, self.user_id)

        assert len(transactions) == 3

        # Check first transaction (user gets money back)
        txn1 = transactions[0]
        assert txn1["amount"] == 12500  # $12.50 in milliunits
        assert txn1["payee_name"] == "Grocery Shopping"
        assert "Paid: $25.00, Owed: $12.50" in txn1["memo"]
        assert txn1["import_id"] == "splitwise_67890"

        # Check second transaction (user owes money)
        txn2 = transactions[1]
        assert txn2["amount"] == -15000  # -$15.00 in milliunits
        assert txn2["payee_name"] == "Restaurant Dinner"
        assert "Paid: $0.00, Owed: $15.00" in txn2["memo"]
        assert txn2["import_id"] == "splitwise_11111"

        # Check third transaction (user gets money back)
        txn3 = transactions[2]
        assert txn3["amount"] == 20000  # $20.00 in milliunits
        assert txn3["payee_name"] == "Gas Station"
        assert "Paid: $40.00, Owed: $20.00" in txn3["memo"]
        assert txn3["import_id"] == "splitwise_22222"

    def test_process_expenses_user_not_involved(self):
        """Test processing expense where user is not involved."""
        expenses = [SAMPLE_EXPENSE_NOT_INVOLVED]

        transactions = self.processor.process_expenses_for_user(expenses, self.user_id)

        assert len(transactions) == 0

    def test_convert_expense_to_transaction_gets_money_back(self):
        """Test converting expense where user gets money back."""
        transaction = self.processor._convert_expense_to_transaction(
            SAMPLE_EXPENSE_GETS_BACK, self.user_id
        )

        assert transaction is not None
        assert transaction["amount"] == 20000  # $20.00 in milliunits (positive)
        assert transaction["payee_name"] == "Gas Station"
        assert "Paid: $40.00, Owed: $20.00" in transaction["memo"]
        assert "Users: John Doe, Jane Smith" in transaction["memo"]
        assert "Splitwise ID: 22222" in transaction["memo"]
        assert transaction["import_id"] == "splitwise_22222"

    def test_convert_expense_to_transaction_owes_money(self):
        """Test converting expense where user owes money."""
        transaction = self.processor._convert_expense_to_transaction(
            SAMPLE_EXPENSE_OWED, self.user_id
        )

        assert transaction is not None
        assert transaction["amount"] == -15000  # -$15.00 in milliunits (negative)
        assert transaction["payee_name"] == "Restaurant Dinner"
        assert "Paid: $0.00, Owed: $15.00" in transaction["memo"]
        assert transaction["import_id"] == "splitwise_11111"

    def test_convert_expense_to_transaction_user_not_involved(self):
        """Test converting expense where user is not involved."""
        transaction = self.processor._convert_expense_to_transaction(
            SAMPLE_EXPENSE_NOT_INVOLVED, self.user_id
        )

        assert transaction is None

    def test_parse_expense_date_success(self):
        """Test successful date parsing."""
        date_str = "2024-01-15T10:30:00Z"
        parsed_date = self.processor._parse_expense_date(date_str)

        assert isinstance(parsed_date, datetime)
        assert parsed_date.year == 2024
        assert parsed_date.month == 1
        assert parsed_date.day == 15

    def test_parse_expense_date_invalid(self):
        """Test date parsing with invalid date."""
        with pytest.raises(DataProcessingError) as exc_info:
            self.processor._parse_expense_date("invalid-date")
        assert "Invalid date format" in str(exc_info.value)

    def test_parse_expense_date_missing(self):
        """Test date parsing with missing date."""
        with pytest.raises(DataProcessingError) as exc_info:
            self.processor._parse_expense_date("")
        assert "Missing expense date" in str(exc_info.value)

    def test_get_user_share_success(self):
        """Test getting user share from expense."""
        share = self.processor._get_user_share(SAMPLE_EXPENSE, self.user_id)

        assert share is not None
        assert share["paid"] == 25.0
        assert share["owed"] == 12.5
        assert share["net"] == 12.5

    def test_get_user_share_not_found(self):
        """Test getting user share when user not in expense."""
        share = self.processor._get_user_share(
            SAMPLE_EXPENSE_NOT_INVOLVED, self.user_id
        )

        assert share is None

    def test_calculate_ynab_amount_positive(self):
        """Test amount calculation for positive net amount."""
        user_share = {"paid": 40.0, "owed": 20.0, "net": 20.0}
        amount = self.processor._calculate_ynab_amount(user_share)

        assert amount == 20000  # $20.00 in milliunits

    def test_calculate_ynab_amount_negative(self):
        """Test amount calculation for negative net amount."""
        user_share = {"paid": 0.0, "owed": 15.0, "net": -15.0}
        amount = self.processor._calculate_ynab_amount(user_share)

        assert amount == -15000  # -$15.00 in milliunits

    def test_calculate_ynab_amount_zero(self):
        """Test amount calculation for zero net amount."""
        user_share = {"paid": 10.0, "owed": 10.0, "net": 0.0}
        amount = self.processor._calculate_ynab_amount(user_share)

        assert amount == 0

    def test_generate_memo_complete(self):
        """Test memo generation with all information."""
        user_share = {"paid": 25.0, "owed": 12.5, "net": 12.5}
        memo = self.processor._generate_memo(SAMPLE_EXPENSE, user_share)

        assert "Paid: $25.00, Owed: $12.50" in memo
        assert "Users: John Doe, Jane Smith" in memo
        assert "Notes: Weekly groceries from the supermarket" in memo
        assert "Splitwise ID: 67890" in memo

    def test_generate_memo_minimal(self):
        """Test memo generation with minimal information."""
        expense = {
            "id": 12345,
            "users": [
                {"user": {"first_name": "John", "last_name": ""}, "user_id": 123}
            ],
        }
        user_share = {"paid": 10.0, "owed": 5.0, "net": 5.0}
        memo = self.processor._generate_memo(expense, user_share)

        assert "Paid: $10.00, Owed: $5.00" in memo
        assert "Users: John" in memo
        assert "Splitwise ID: 12345" in memo

    def test_filter_duplicates(self):
        """Test filtering duplicate transactions."""
        transactions = [
            {"import_id": "splitwise_1", "payee_name": "Test 1"},
            {"import_id": "splitwise_2", "payee_name": "Test 2"},
            {"import_id": "splitwise_3", "payee_name": "Test 3"},
        ]
        existing_import_ids = ["splitwise_2"]

        filtered = self.processor.filter_duplicates(transactions, existing_import_ids)

        assert len(filtered) == 2
        assert filtered[0]["import_id"] == "splitwise_1"
        assert filtered[1]["import_id"] == "splitwise_3"

    def test_validate_transactions_success(self):
        """Test successful transaction validation."""
        transactions = [
            {
                "amount": 15000,
                "payee_name": "Test Payee",
                "memo": "Test memo",
                "date": datetime(2024, 1, 1),
                "import_id": "splitwise_123",
            }
        ]

        # Should not raise any exception
        self.processor.validate_transactions(transactions)

    def test_validate_transactions_missing_field(self):
        """Test validation fails with missing required field."""
        transactions = [
            {
                "amount": 15000,
                "payee_name": "Test Payee",
                # Missing memo field
                "date": datetime(2024, 1, 1),
                "import_id": "splitwise_123",
            }
        ]

        with pytest.raises(DataProcessingError) as exc_info:
            self.processor.validate_transactions(transactions)
        assert "missing required field: memo" in str(exc_info.value)

    def test_validate_transactions_invalid_amount_type(self):
        """Test validation fails with invalid amount type."""
        transactions = [
            {
                "amount": "15000",  # Should be int, not string
                "payee_name": "Test Payee",
                "memo": "Test memo",
                "date": datetime(2024, 1, 1),
                "import_id": "splitwise_123",
            }
        ]

        with pytest.raises(DataProcessingError) as exc_info:
            self.processor.validate_transactions(transactions)
        assert "amount must be integer" in str(exc_info.value)

    def test_validate_transactions_empty_payee_name(self):
        """Test validation fails with empty payee name."""
        transactions = [
            {
                "amount": 15000,
                "payee_name": "   ",  # Empty/whitespace string
                "memo": "Test memo",
                "date": datetime(2024, 1, 1),
                "import_id": "splitwise_123",
            }
        ]

        with pytest.raises(DataProcessingError) as exc_info:
            self.processor.validate_transactions(transactions)
        assert "payee_name must be non-empty string" in str(exc_info.value)
