"""Duplicate transaction detection system."""

from datetime import datetime
from typing import Any, Dict, List, Set

from ..utils.exceptions import DuplicateTransactionError
from ..utils.logger import LoggerMixin


class DuplicateDetector(LoggerMixin):
    """Handles duplicate transaction detection using multiple strategies."""
    
    def __init__(self) -> None:
        """Initialize duplicate detector."""
        self.processed_import_ids: Set[str] = set()
        self.logger.info("Duplicate detector initialized")
    
    def generate_import_id(self, expense_id: str) -> str:
        """Generate import ID for a Splitwise expense.
        
        Args:
            expense_id: Splitwise expense ID
            
        Returns:
            Import ID string in format 'splitwise_{expense_id}'
        """
        return f"splitwise_{expense_id}"
    
    def filter_existing_transactions(
        self,
        transactions: List[Dict[str, Any]],
        existing_import_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter out transactions that already exist in YNAB.
        
        Args:
            transactions: List of transaction dictionaries
            existing_import_ids: List of import IDs that already exist in YNAB
            
        Returns:
            List of transactions that don't already exist
        """
        existing_set = set(existing_import_ids)
        filtered_transactions = []
        
        for txn in transactions:
            import_id = txn.get("import_id")
            if import_id not in existing_set:
                filtered_transactions.append(txn)
            else:
                self.logger.info(f"Skipping duplicate transaction with import_id: {import_id}")
        
        self.logger.info(
            f"Filtered {len(transactions) - len(filtered_transactions)} duplicate transactions, "
            f"{len(filtered_transactions)} remaining"
        )
        
        return filtered_transactions
    
    def detect_duplicates_by_content(
        self,
        new_transactions: List[Dict[str, Any]],
        existing_transactions: List[Dict[str, Any]],
        tolerance_days: int = 1
    ) -> List[Dict[str, Any]]:
        """Detect duplicates by comparing transaction content.
        
        This is a fallback method when import_id matching isn't sufficient.
        
        Args:
            new_transactions: List of new transactions to check
            existing_transactions: List of existing transactions
            tolerance_days: Number of days tolerance for date matching
            
        Returns:
            List of new transactions that are not duplicates
        """
        non_duplicate_transactions = []
        
        for new_txn in new_transactions:
            is_duplicate = False
            
            for existing_txn in existing_transactions:
                if self._is_content_duplicate(new_txn, existing_txn, tolerance_days):
                    self.logger.info(
                        f"Detected content duplicate: {new_txn.get('payee_name')} "
                        f"on {new_txn.get('date')} for ${new_txn.get('amount', 0)/1000:.2f}"
                    )
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                non_duplicate_transactions.append(new_txn)
        
        self.logger.info(
            f"Content-based duplicate detection: {len(new_transactions) - len(non_duplicate_transactions)} "
            f"duplicates found, {len(non_duplicate_transactions)} unique transactions"
        )
        
        return non_duplicate_transactions
    
    def _is_content_duplicate(
        self,
        txn1: Dict[str, Any],
        txn2: Dict[str, Any],
        tolerance_days: int
    ) -> bool:
        """Check if two transactions are duplicates based on content.
        
        Args:
            txn1: First transaction
            txn2: Second transaction
            tolerance_days: Number of days tolerance for date matching
            
        Returns:
            True if transactions are likely duplicates
        """
        # Check amount (must be exact)
        if txn1.get("amount") != txn2.get("amount"):
            return False
        
        # Check payee (case-insensitive)
        payee1 = txn1.get("payee_name", "").lower().strip()
        payee2 = txn2.get("payee_name", "").lower().strip()
        if payee1 != payee2:
            return False
        
        # Check date (within tolerance)
        date1 = txn1.get("date")
        date2 = txn2.get("date")
        
        if isinstance(date1, datetime):
            date1 = date1.date()
        if isinstance(date2, datetime):
            date2 = date2.date()
        
        if date1 and date2:
            date_diff = abs((date1 - date2).days)
            if date_diff > tolerance_days:
                return False
        
        # Check memo similarity (optional, for additional confidence)
        memo1 = txn1.get("memo", "").lower().strip()
        memo2 = txn2.get("memo", "").lower().strip()
        
        # If both have memos, they should be similar
        if memo1 and memo2:
            # Simple similarity check: check if one memo contains key parts of the other
            memo1_words = set(memo1.split())
            memo2_words = set(memo2.split())
            common_words = memo1_words.intersection(memo2_words)
            
            # If they share significant words, consider them similar
            if len(common_words) < min(len(memo1_words), len(memo2_words)) * 0.5:
                return False
        
        return True
    
    def validate_import_ids(self, transactions: List[Dict[str, Any]]) -> None:
        """Validate that all transactions have valid import IDs.
        
        Args:
            transactions: List of transactions to validate
            
        Raises:
            DuplicateTransactionError: If any transaction has invalid import_id
        """
        for i, txn in enumerate(transactions):
            import_id = txn.get("import_id")
            
            if not import_id:
                raise DuplicateTransactionError(
                    f"Transaction {i} missing import_id",
                    details=f"Transaction: {txn.get('payee_name')} - ${txn.get('amount', 0)/1000:.2f}"
                )
            
            if not isinstance(import_id, str) or not import_id.startswith("splitwise_"):
                raise DuplicateTransactionError(
                    f"Transaction {i} has invalid import_id format: {import_id}",
                    details="Import ID should be in format 'splitwise_{expense_id}'"
                )
            
            # Check for duplicates within the batch
            if import_id in self.processed_import_ids:
                raise DuplicateTransactionError(
                    f"Duplicate import_id in batch: {import_id}",
                    details=f"Transaction: {txn.get('payee_name')} - ${txn.get('amount', 0)/1000:.2f}"
                )
            
            self.processed_import_ids.add(import_id)
        
        self.logger.info(f"Validated {len(transactions)} transactions with unique import IDs")
    
    def reset_processed_ids(self) -> None:
        """Reset the set of processed import IDs."""
        self.processed_import_ids.clear()
        self.logger.debug("Reset processed import IDs")
    
    def get_import_ids_from_transactions(self, transactions: List[Dict[str, Any]]) -> List[str]:
        """Extract import IDs from a list of transactions.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of import IDs
        """
        import_ids = []
        for txn in transactions:
            import_id = txn.get("import_id")
            if import_id:
                import_ids.append(import_id)
        
        return import_ids