"""Command line interface for YNAB-Splitwise integration."""

import sys
from datetime import datetime
from typing import Optional

import click
from dateutil.parser import parse as parse_date

from ..auth.config import Config
from ..clients.splitwise import SplitwiseClient
from ..clients.ynab_client import YnabClient
from ..processors.transaction_processor import TransactionProcessor
from ..utils.exceptions import YnabSplitwiseError
from ..utils.logger import setup_logger


@click.command()
@click.option(
    "--start-date",
    type=str,
    help="Start date for syncing (YYYY-MM-DD format). If not provided, you will be prompted."
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview transactions without importing them to YNAB."
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging output."
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Set logging level."
)
@click.option(
    "--skip-filter",
    is_flag=True,
    help="Skip transaction filtering and import all found transactions."
)
def main(
    start_date: Optional[str],
    dry_run: bool,
    verbose: bool,
    log_level: str,
    skip_filter: bool
) -> None:
    """Sync Splitwise expenses to YNAB.
    
    This tool fetches your Splitwise expenses and creates corresponding
    transactions in your YNAB 'Splitwise (Wallet)' account.
    """
    # Set up logging
    if verbose:
        log_level = "DEBUG"
    
    logger = setup_logger(level=log_level)
    
    try:
        # Display welcome message
        click.echo("🔄 YNAB-Splitwise Integration")
        click.echo("=" * 40)
        
        # Load and validate configuration
        logger.info("Loading configuration...")
        config = Config()
        config.validate()
        click.echo("✅ Configuration loaded successfully")
        
        # Get start date from user if not provided
        if not start_date:
            start_date = click.prompt(
                "Enter start date for syncing expenses (YYYY-MM-DD)",
                type=str
            )
        
        # Parse and validate start date
        try:
            start_datetime = parse_date(start_date)
            logger.info(f"Syncing expenses from {start_datetime.date()}")
            click.echo(f"📅 Start date: {start_datetime.date()}")
        except Exception as e:
            click.echo(f"❌ Invalid date format: {start_date}")
            click.echo("Please use YYYY-MM-DD format (e.g., 2024-01-01)")
            sys.exit(1)
        
        # Initialize clients
        logger.info("Initializing API clients...")
        splitwise_client = SplitwiseClient(config)
        ynab_client = YnabClient(config)
        processor = TransactionProcessor()
        
        # Test connections and get user info
        click.echo("🔗 Testing API connections...")
        
        # Test Splitwise connection and get current user
        current_user = splitwise_client.get_current_user()
        user_id = current_user["id"]
        user_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
        click.echo(f"✅ Connected to Splitwise as: {user_name} ({current_user.get('email', '')})")
        
        # Test YNAB connection and verify account
        ynab_account_id = ynab_client.get_account_id(config.ynab_account_name)
        click.echo(f"✅ Found YNAB account: '{config.ynab_account_name}'")
        
        # Fetch expenses from Splitwise
        click.echo(f"📥 Fetching expenses from {start_datetime.date()}...")
        expenses = splitwise_client.get_all_expenses_since(start_datetime)
        
        if not expenses:
            click.echo("ℹ️  No expenses found for the specified date range")
            return
        
        click.echo(f"📊 Found {len(expenses)} expenses")
        
        # Process expenses into transactions
        click.echo("🔄 Processing expenses...")
        transactions = processor.process_expenses_for_user(expenses, user_id)
        
        if not transactions:
            click.echo("ℹ️  No transactions to import (you have no share in the found expenses)")
            return
        
        click.echo(f"💰 Processed {len(transactions)} transactions")
        
        # Check for existing transactions to avoid duplicates
        click.echo("🔍 Checking for existing transactions...")
        import_ids = processor.duplicate_detector.get_import_ids_from_transactions(transactions)
        existing_import_ids = ynab_client.get_transactions_by_import_id(import_ids)
        
        # Filter out duplicates
        new_transactions = processor.filter_duplicates(transactions, existing_import_ids)
        
        duplicates_count = len(transactions) - len(new_transactions)
        if duplicates_count > 0:
            click.echo(f"⚠️  Skipped {duplicates_count} duplicate transactions")
        
        if not new_transactions:
            click.echo("ℹ️  All transactions already exist in YNAB")
            return
        
        click.echo(f"📝 {len(new_transactions)} new transactions to import")
        
        # Display transaction preview
        display_transaction_preview(new_transactions)
        
        if dry_run:
            click.echo("\\n🔍 Dry run completed - no transactions were imported")
            return
        
        # Let user filter transactions by date (unless skipped)
        if skip_filter:
            filtered_transactions = new_transactions
            click.echo("⏭️  Skipping transaction filtering (--skip-filter enabled)")
        else:
            filtered_transactions = filter_transactions_by_date(new_transactions)
        
        if not filtered_transactions:
            click.echo("❌ No transactions selected for import")
            return
        
        # Show final selection if different from original
        if len(filtered_transactions) != len(new_transactions):
            click.echo(f"\\n📋 Selected {len(filtered_transactions)} transactions:")
            display_transaction_preview(filtered_transactions)
        
        # Confirm import
        if not click.confirm(f"\\nImport {len(filtered_transactions)} transactions to YNAB?"):
            click.echo("❌ Import cancelled")
            return
        
        # Validate transactions before import
        processor.validate_transactions(filtered_transactions)
        
        # Import transactions to YNAB
        click.echo("📤 Importing transactions to YNAB...")
        
        if len(filtered_transactions) == 1:
            # Single transaction
            txn = filtered_transactions[0]
            created_txn = ynab_client.create_transaction(
                amount=txn["amount"],
                payee_name=txn["payee_name"],
                memo=txn["memo"],
                date=txn["date"],
                import_id=txn["import_id"]
            )
            click.echo(f"✅ Created transaction: {created_txn['payee_name']}")
        else:
            # Batch import
            created_transactions = ynab_client.create_transactions_batch(filtered_transactions)
            click.echo(f"✅ Successfully imported {len(created_transactions)} transactions")
        
        # Success message
        click.echo("\\n🎉 Sync completed successfully!")
        click.echo(f"   • {len(filtered_transactions)} transactions imported")
        click.echo(f"   • {duplicates_count} duplicates skipped")
        click.echo("   • All transactions are in 'Review' status in YNAB")
        
    except YnabSplitwiseError as e:
        logger.error(f"Application error: {e.message}")
        click.echo(f"❌ Error: {e.message}")
        if e.details:
            click.echo(f"   Details: {e.details}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        click.echo(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


def filter_transactions_by_date(transactions: list) -> list:
    """Allow user to filter transactions by date range.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Filtered list of transactions
    """
    if not transactions:
        return transactions
    
    # Sort transactions by date for easier selection
    sorted_transactions = sorted(transactions, key=lambda x: x['date'])
    
    click.echo("\\n🗓️  Transaction Date Filtering")
    click.echo("=" * 40)
    
    # Show date range
    start_date = sorted_transactions[0]['date'].strftime('%Y-%m-%d')
    end_date = sorted_transactions[-1]['date'].strftime('%Y-%m-%d')
    click.echo(f"📅 Transactions from {start_date} to {end_date}")
    
    # Filtering options
    choice = click.prompt(
        "\\nHow would you like to filter?\\n"
        "1. Import all transactions\\n"
        "2. Import transactions before a specific date\\n"
        "3. Import transactions after a specific date\\n"
        "4. Import transactions between two dates\\n"
        "5. Cancel import\\n"
        "Enter choice (1-5)",
        type=click.Choice(['1', '2', '3', '4', '5'])
    )
    
    if choice == '1':
        return transactions
    elif choice == '5':
        return []
    
    try:
        if choice == '2':
            # Before a specific date
            cutoff_date = click.prompt(
                "Enter cutoff date (YYYY-MM-DD) - import transactions BEFORE this date",
                type=str
            )
            cutoff = parse_date(cutoff_date).date()
            filtered = [txn for txn in sorted_transactions if txn['date'].date() < cutoff]
            
        elif choice == '3':
            # After a specific date
            cutoff_date = click.prompt(
                "Enter cutoff date (YYYY-MM-DD) - import transactions AFTER this date",
                type=str
            )
            cutoff = parse_date(cutoff_date).date()
            filtered = [txn for txn in sorted_transactions if txn['date'].date() > cutoff]
            
        elif choice == '4':
            # Between two dates
            start_filter = click.prompt(
                "Enter start date (YYYY-MM-DD) - import transactions FROM this date",
                type=str
            )
            end_filter = click.prompt(
                "Enter end date (YYYY-MM-DD) - import transactions TO this date",
                type=str
            )
            start_cutoff = parse_date(start_filter).date()
            end_cutoff = parse_date(end_filter).date()
            filtered = [
                txn for txn in sorted_transactions 
                if start_cutoff <= txn['date'].date() <= end_cutoff
            ]
        
        click.echo(f"\\n✅ Filtered to {len(filtered)} transactions")
        return filtered
        
    except Exception as e:
        click.echo(f"❌ Invalid date format: {e}")
        click.echo("Using all transactions instead...")
        return transactions


def display_transaction_preview(transactions: list) -> None:
    """Display a preview of transactions to be imported.
    
    Args:
        transactions: List of transaction dictionaries
    """
    click.echo("\\n📋 Transaction Preview:")
    click.echo("-" * 80)
    
    total_amount = 0
    
    for i, txn in enumerate(transactions, 1):
        amount = txn["amount"] / 1000  # Convert from milliunits
        total_amount += amount
        
        # Format amount with proper sign
        amount_str = f"${abs(amount):.2f}"
        if amount >= 0:
            amount_str = f"+{amount_str}"
        else:
            amount_str = f"-{amount_str}"
        
        click.echo(f"{i:2d}. {txn['date'].strftime('%Y-%m-%d')} | "
                  f"{amount_str:>10s} | {txn['payee_name']}")
        
        # Show memo preview (first 60 chars)
        memo = txn.get("memo", "")
        if len(memo) > 60:
            memo = memo[:57] + "..."
        click.echo(f"     Memo: {memo}")
        click.echo()
    
    click.echo("-" * 80)
    total_str = f"${abs(total_amount):.2f}"
    if total_amount >= 0:
        total_str = f"+{total_str}"
    else:
        total_str = f"-{total_str}"
    click.echo(f"Total: {total_str}")


if __name__ == "__main__":
    main()