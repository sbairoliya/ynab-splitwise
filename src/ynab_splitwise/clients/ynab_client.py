"""YNAB API client."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import ynab
from ynab import PostTransactionsWrapper, SaveTransactionWithOptionalFields, ApiException

from ..auth.config import Config
from ..utils.exceptions import AccountNotFoundError, YnabAPIError
from ..utils.logger import LoggerMixin


class YnabClient(LoggerMixin):
    """Client for interacting with the YNAB API."""
    
    def __init__(self, config: Config) -> None:
        """Initialize YNAB client.
        
        Args:
            config: Configuration object with API credentials
        """
        self.config = config
        
        # Configure YNAB SDK
        ynab_config = ynab.Configuration(
            host=config.ynab_api_url,
            access_token=config.ynab_access_token
        )
        
        self.api_client = ynab.ApiClient(ynab_config)
        self.accounts_api = ynab.AccountsApi(self.api_client)
        self.transactions_api = ynab.TransactionsApi(self.api_client)
        self.budgets_api = ynab.BudgetsApi(self.api_client)
        
        self._budget_id: Optional[str] = None
        self._account_id: Optional[str] = None
        
        self.logger.info("YNAB client initialized")
    
    def _handle_api_exception(self, e: ApiException, operation: str) -> None:
        """Handle YNAB API exceptions.
        
        Args:
            e: The API exception
            operation: Description of the operation that failed
            
        Raises:
            YnabAPIError: With detailed error information
        """
        error_msg = f"YNAB API error during {operation}: {e.reason}"
        details = f"Status: {e.status}, Body: {e.body}"
        self.logger.error(f"{error_msg} - {details}")
        raise YnabAPIError(error_msg, details=details)
    
    def get_budget_id(self) -> str:
        """Get the budget ID (uses default or last-used budget).
        
        Returns:
            Budget ID string
            
        Raises:
            YnabAPIError: If unable to get budget
        """
        if self._budget_id:
            return self._budget_id
        
        try:
            self.logger.info("Fetching budget information")
            # Use "last-used" budget as specified in YNAB API docs
            self._budget_id = "last-used"
            
            # Verify the budget exists by making a test call
            self.budgets_api.get_budget_by_id(self._budget_id)
            self.logger.info(f"Using budget: {self._budget_id}")
            return self._budget_id
            
        except ApiException as e:
            self._handle_api_exception(e, "getting budget")
    
    def get_account_id(self, account_name: str) -> str:
        """Get account ID by name.
        
        Args:
            account_name: Name of the account to find
            
        Returns:
            Account ID string
            
        Raises:
            AccountNotFoundError: If account is not found
            YnabAPIError: If API request fails
        """
        if self._account_id:
            return self._account_id
        
        try:
            budget_id = self.get_budget_id()
            self.logger.info(f"Looking for account: '{account_name}'")
            
            accounts_response = self.accounts_api.get_accounts(budget_id)
            
            for account in accounts_response.data.accounts:
                if account.name == account_name:
                    self._account_id = account.id
                    self.logger.info(f"Found account '{account_name}' with ID: {self._account_id}")
                    return self._account_id
            
            # Account not found
            available_accounts = [acc.name for acc in accounts_response.data.accounts]
            error_msg = f"Account '{account_name}' not found"
            details = f"Available accounts: {', '.join(available_accounts)}"
            self.logger.error(f"{error_msg}. {details}")
            raise AccountNotFoundError(error_msg, details=details)
            
        except ApiException as e:
            self._handle_api_exception(e, f"searching for account '{account_name}'")
    
    def create_transaction(
        self,
        amount: int,  # Amount in milliunits (e.g., $1.00 = 1000)
        payee_name: str,
        memo: str,
        date: datetime,
        import_id: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a single transaction in YNAB.
        
        Args:
            amount: Transaction amount in milliunits (negative for outflow)
            payee_name: Name of the payee
            memo: Transaction memo/notes
            date: Transaction date
            import_id: Unique import ID for duplicate detection
            account_id: Account ID (uses default if not provided)
            
        Returns:
            Created transaction data
            
        Raises:
            YnabAPIError: If transaction creation fails
        """
        try:
            budget_id = self.get_budget_id()
            
            if not account_id:
                account_id = self.get_account_id(self.config.ynab_account_name)
            
            # Create transaction object
            transaction = SaveTransactionWithOptionalFields(
                account_id=account_id,
                amount=amount,
                payee_name=payee_name,
                memo=memo,
                date=date.date(),
                import_id=import_id,
                cleared="uncleared"  # Let user review in YNAB
            )
            
            # Wrap transaction for API call
            wrapper = PostTransactionsWrapper(transaction=transaction)
            
            self.logger.info(f"Creating transaction: {payee_name} - ${amount/1000:.2f}")
            self.logger.debug(f"Transaction details: amount={amount}, memo='{memo}', import_id='{import_id}'")
            
            # Create transaction
            response = self.transactions_api.create_transaction(budget_id, wrapper)
            
            if response.data.transaction:
                created_transaction = response.data.transaction
                self.logger.info(f"Successfully created transaction with ID: {created_transaction.id}")
                return {
                    "id": created_transaction.id,
                    "amount": created_transaction.amount,
                    "payee_name": created_transaction.payee_name,
                    "memo": created_transaction.memo,
                    "date": created_transaction.date,
                    "import_id": created_transaction.import_id
                }
            else:
                raise YnabAPIError("No transaction data in response")
                
        except ApiException as e:
            self._handle_api_exception(e, "creating transaction")
    
    def create_transactions_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple transactions in a single API call.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of created transaction data
            
        Raises:
            YnabAPIError: If batch creation fails
        """
        if not transactions:
            self.logger.info("No transactions to create")
            return []
        
        try:
            budget_id = self.get_budget_id()
            account_id = self.get_account_id(self.config.ynab_account_name)
            
            # Convert to SaveTransaction objects
            save_transactions = []
            for txn in transactions:
                save_transaction = SaveTransactionWithOptionalFields(
                    account_id=account_id,
                    amount=txn["amount"],
                    payee_name=txn["payee_name"],
                    memo=txn["memo"],
                    date=txn["date"].date() if isinstance(txn["date"], datetime) else txn["date"],
                    import_id=txn["import_id"],
                    cleared="uncleared"
                )
                save_transactions.append(save_transaction)
            
            # Wrap transactions for API call
            wrapper = PostTransactionsWrapper(transactions=save_transactions)
            
            self.logger.info(f"Creating batch of {len(transactions)} transactions")
            
            # Create transactions
            response = self.transactions_api.create_transaction(budget_id, wrapper)
            
            created_transactions = []
            if response.data.transactions:
                for txn in response.data.transactions:
                    created_transactions.append({
                        "id": txn.id,
                        "amount": txn.amount,
                        "payee_name": txn.payee_name,
                        "memo": txn.memo,
                        "date": txn.date,
                        "import_id": txn.import_id
                    })
                
                self.logger.info(f"Successfully created {len(created_transactions)} transactions")
            
            return created_transactions
            
        except ApiException as e:
            self._handle_api_exception(e, "creating transaction batch")
    
    def get_transactions_by_import_id(self, import_ids: List[str]) -> List[str]:
        """Check which import IDs already exist in YNAB.
        
        Args:
            import_ids: List of import IDs to check
            
        Returns:
            List of import IDs that already exist
            
        Raises:
            YnabAPIError: If API request fails
        """
        if not import_ids:
            return []
        
        try:
            budget_id = self.get_budget_id()
            account_id = self.get_account_id(self.config.ynab_account_name)
            
            self.logger.info(f"Checking for existing transactions with {len(import_ids)} import IDs")
            
            # Get all transactions for the account
            transactions_response = self.transactions_api.get_transactions_by_account(
                budget_id, 
                account_id
            )
            
            existing_import_ids = []
            for txn in transactions_response.data.transactions:
                if txn.import_id and txn.import_id in import_ids:
                    existing_import_ids.append(txn.import_id)
            
            self.logger.info(f"Found {len(existing_import_ids)} existing transactions")
            return existing_import_ids
            
        except ApiException as e:
            self._handle_api_exception(e, "checking existing transactions")