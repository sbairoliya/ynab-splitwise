"""Tests for duplicate detector."""

import pytest
from datetime import datetime, date

from src.ynab_splitwise.processors.duplicate_detector import DuplicateDetector
from src.ynab_splitwise.utils.exceptions import DuplicateTransactionError


class TestDuplicateDetector:
    """Test duplicate detection logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = DuplicateDetector()
    
    def test_generate_import_id(self):
        """Test import ID generation."""
        import_id = self.detector.generate_import_id("12345")
        assert import_id == "splitwise_12345"
    
    def test_filter_existing_transactions(self):
        """Test filtering existing transactions."""
        transactions = [
            {"import_id": "splitwise_1", "payee_name": "Test 1"},
            {"import_id": "splitwise_2", "payee_name": "Test 2"},
            {"import_id": "splitwise_3", "payee_name": "Test 3"}
        ]
        existing_import_ids = ["splitwise_2"]
        
        filtered = self.detector.filter_existing_transactions(
            transactions, existing_import_ids
        )
        
        assert len(filtered) == 2
        assert filtered[0]["import_id"] == "splitwise_1"
        assert filtered[1]["import_id"] == "splitwise_3"
    
    def test_filter_existing_transactions_empty_existing(self):
        """Test filtering with no existing transactions."""
        transactions = [
            {"import_id": "splitwise_1", "payee_name": "Test 1"},
            {"import_id": "splitwise_2", "payee_name": "Test 2"}
        ]
        existing_import_ids = []
        
        filtered = self.detector.filter_existing_transactions(
            transactions, existing_import_ids
        )
        
        assert len(filtered) == 2
        assert filtered == transactions
    
    def test_detect_duplicates_by_content_exact_match(self):
        """Test content-based duplicate detection with exact match."""
        new_transactions = [
            {
                "amount": 15000,
                "payee_name": "Restaurant",
                "date": date(2024, 1, 15),
                "memo": "Dinner with friends"
            }
        ]
        existing_transactions = [
            {
                "amount": 15000,
                "payee_name": "Restaurant",
                "date": date(2024, 1, 15),
                "memo": "Dinner with friends"
            }
        ]
        
        non_duplicates = self.detector.detect_duplicates_by_content(
            new_transactions, existing_transactions
        )
        
        assert len(non_duplicates) == 0
    
    def test_detect_duplicates_by_content_different_amount(self):
        """Test content-based detection with different amounts."""
        new_transactions = [
            {
                "amount": 15000,
                "payee_name": "Restaurant",
                "date": date(2024, 1, 15),
                "memo": "Dinner"
            }
        ]
        existing_transactions = [
            {
                "amount": 20000,  # Different amount
                "payee_name": "Restaurant",
                "date": date(2024, 1, 15),
                "memo": "Dinner"
            }
        ]
        
        non_duplicates = self.detector.detect_duplicates_by_content(
            new_transactions, existing_transactions
        )
        
        assert len(non_duplicates) == 1
    
    def test_detect_duplicates_by_content_date_tolerance(self):
        """Test content-based detection with date tolerance."""
        new_transactions = [
            {
                "amount": 15000,
                "payee_name": "Restaurant",
                "date": date(2024, 1, 15),
                "memo": "Dinner"
            }
        ]
        existing_transactions = [
            {
                "amount": 15000,
                "payee_name": "Restaurant",
                "date": date(2024, 1, 16),  # 1 day difference
                "memo": "Dinner"
            }
        ]
        
        # Within tolerance (1 day)
        non_duplicates = self.detector.detect_duplicates_by_content(
            new_transactions, existing_transactions, tolerance_days=1
        )
        assert len(non_duplicates) == 0
        
        # Outside tolerance (0 days)
        non_duplicates = self.detector.detect_duplicates_by_content(
            new_transactions, existing_transactions, tolerance_days=0
        )
        assert len(non_duplicates) == 1
    
    def test_is_content_duplicate_case_insensitive_payee(self):
        """Test duplicate detection is case-insensitive for payee names."""
        txn1 = {
            "amount": 15000,
            "payee_name": "Restaurant",
            "date": date(2024, 1, 15)
        }
        txn2 = {
            "amount": 15000,
            "payee_name": "RESTAURANT",  # Different case
            "date": date(2024, 1, 15)
        }
        
        is_duplicate = self.detector._is_content_duplicate(txn1, txn2, 1)
        assert is_duplicate is True
    
    def test_is_content_duplicate_memo_similarity(self):
        """Test duplicate detection with similar memos."""
        txn1 = {
            "amount": 15000,
            "payee_name": "Restaurant",
            "date": date(2024, 1, 15),
            "memo": "dinner with friends tonight"
        }
        txn2 = {
            "amount": 15000,
            "payee_name": "Restaurant",
            "date": date(2024, 1, 15),
            "memo": "dinner friends"  # Similar but shorter
        }
        
        is_duplicate = self.detector._is_content_duplicate(txn1, txn2, 1)
        assert is_duplicate is True
    
    def test_validate_import_ids_success(self):
        """Test successful import ID validation."""
        transactions = [
            {"import_id": "splitwise_123", "payee_name": "Test 1", "amount": 1000},
            {"import_id": "splitwise_456", "payee_name": "Test 2", "amount": 2000}
        ]
        
        # Should not raise any exception
        self.detector.validate_import_ids(transactions)
    
    def test_validate_import_ids_missing(self):
        """Test validation fails with missing import ID."""
        transactions = [
            {"payee_name": "Test 1", "amount": 1000}  # Missing import_id
        ]
        
        with pytest.raises(DuplicateTransactionError) as exc_info:
            self.detector.validate_import_ids(transactions)
        assert "missing import_id" in str(exc_info.value)
    
    def test_validate_import_ids_invalid_format(self):
        """Test validation fails with invalid import ID format."""
        transactions = [
            {"import_id": "invalid_format", "payee_name": "Test 1", "amount": 1000}
        ]
        
        with pytest.raises(DuplicateTransactionError) as exc_info:
            self.detector.validate_import_ids(transactions)
        assert "invalid import_id format" in str(exc_info.value)
    
    def test_validate_import_ids_duplicate_in_batch(self):
        """Test validation fails with duplicate import IDs in batch."""
        transactions = [
            {"import_id": "splitwise_123", "payee_name": "Test 1", "amount": 1000},
            {"import_id": "splitwise_123", "payee_name": "Test 2", "amount": 2000}  # Duplicate
        ]
        
        with pytest.raises(DuplicateTransactionError) as exc_info:
            self.detector.validate_import_ids(transactions)
        assert "Duplicate import_id in batch" in str(exc_info.value)
    
    def test_reset_processed_ids(self):
        """Test resetting processed IDs."""
        transactions = [
            {"import_id": "splitwise_123", "payee_name": "Test 1", "amount": 1000}
        ]
        
        # First validation should succeed
        self.detector.validate_import_ids(transactions)
        
        # Second validation should fail without reset
        with pytest.raises(DuplicateTransactionError):
            self.detector.validate_import_ids(transactions)
        
        # After reset, validation should succeed again
        self.detector.reset_processed_ids()
        self.detector.validate_import_ids(transactions)
    
    def test_get_import_ids_from_transactions(self):
        """Test extracting import IDs from transactions."""
        transactions = [
            {"import_id": "splitwise_123", "payee_name": "Test 1"},
            {"import_id": "splitwise_456", "payee_name": "Test 2"},
            {"payee_name": "Test 3"}  # No import_id
        ]
        
        import_ids = self.detector.get_import_ids_from_transactions(transactions)
        
        assert len(import_ids) == 2
        assert "splitwise_123" in import_ids
        assert "splitwise_456" in import_ids