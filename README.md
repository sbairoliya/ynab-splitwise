# YNAB-Splitwise Integration

Automatically sync your Splitwise expenses to YNAB, importing your share of each expense with detailed transaction notes.

## Features

- Import your owed share and money you get back from Splitwise
- Detailed transaction memos with paid amounts and users involved
- Robust duplicate detection using import IDs
- User-friendly CLI with date range selection
- Comprehensive error handling and logging
- Transactions appear in YNAB's review section for approval

## Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- YNAB account with API access
- Splitwise account with API access
- A YNAB account named "Splitwise (Wallet)" (or customize the name)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ynab-splitwise

# Install dependencies with uv
uv sync

# For development (includes all dev dependencies)
uv sync --all-extras
```

### 3. Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Get your API credentials:
   - **Splitwise API Key**: Visit [Splitwise Apps](https://secure.splitwise.com/apps) and create a new app
   - **YNAB Access Token**: Visit [YNAB Developer Settings](https://app.ynab.com/settings/developer) and create a personal access token

3. Edit `.env` with your credentials:
   ```bash
   SPLITWISE_API_KEY=your_splitwise_api_key_here
   YNAB_ACCESS_TOKEN=your_ynab_access_token_here
   ```

4. The environment variables will be automatically loaded when using `uv run --env-file .env`

### 4. Run the Sync

#### Using uv with .env file (Recommended)
```bash
# Run the sync (you'll be prompted for start date)
uv run --env-file .env python main.py

# Or specify the start date directly
uv run --env-file .env python main.py --start-date 2024-01-01

# Preview transactions without importing
uv run --env-file .env python main.py --dry-run --start-date 2024-01-01

# Enable verbose logging
uv run --env-file .env python main.py --verbose --start-date 2024-01-01
```

#### Alternative: Using environment variables directly
```bash
# Set environment variables directly
export SPLITWISE_API_KEY="your_key_here"
export YNAB_ACCESS_TOKEN="your_token_here"

# Then run normally
uv run python main.py --start-date 2024-01-01
```

## How It Works

1. **Fetch Expenses**: Retrieves all Splitwise expenses since your specified start date
2. **Calculate Shares**: Determines your owed amount or money you get back for each expense
3. **Transform Data**: Converts Splitwise expenses to YNAB transactions with detailed memos
4. **Detect Duplicates**: Uses import IDs to prevent duplicate transactions
5. **Import to YNAB**: Creates transactions in your "Splitwise (Wallet)" account

## Transaction Details

Each imported transaction includes:

- **Amount**: Your net share (negative for owed, positive for money back)
- **Payee**: Expense description from Splitwise
- **Memo**: Detailed information including:
  - Amount you paid and owed
  - List of users involved
  - Original expense notes
  - Splitwise expense ID for reference
- **Import ID**: Unique identifier for duplicate prevention (`splitwise_{expense_id}`)

## CLI Options

```bash
uv run --env-file .env python main.py [OPTIONS]

Options:
  --start-date TEXT     Start date for syncing (YYYY-MM-DD format)
  --dry-run            Preview transactions without importing
  --verbose            Enable verbose logging
  --log-level LEVEL    Set logging level (DEBUG, INFO, WARNING, ERROR)
  --skip-filter        Skip transaction filtering and import all found transactions
  --help               Show help message
```

## Transaction Filtering

After fetching transactions, you can choose which ones to import based on their position in the numbered list:

1. **Import all transactions** - Import everything found
2. **Import before position #** - Only transactions before a specific number (e.g., before #5)
3. **Import after position #** - Only transactions after a specific number (e.g., after #3)
4. **Import between positions** - Transactions within a range (e.g., #2 to #8)
5. **Import specific numbers** - Select individual transactions (e.g., 1,3,5)
6. **Cancel import** - Skip importing altogether

### Example Filtering Interface
```
📋 Transaction Preview:
--------------------------------------------------------------------------------
 1. 2024-01-15 |    -$12.50 | Weekly groceries
 2. 2024-01-18 |    +$25.00 | Dinner split refund
 3. 2024-01-20 |    -$8.75  | Coffee meeting
 4. 2024-01-22 |    -$45.00 | Uber ride home
 5. 2024-01-25 |    +$15.50 | Movie tickets refund

🔢 Transaction Position Filtering
========================================
Select which transactions to import from the numbered list above:

How would you like to filter?
1. Import all transactions
2. Import transactions before position # (e.g., before #5)
3. Import transactions after position # (e.g., after #3)
4. Import transactions between positions (e.g., #2 to #8)
5. Import specific transaction numbers (e.g., 1,3,5)
6. Cancel import
Enter choice (1-6): 5

Enter transaction numbers separated by commas (e.g., 1,3,5): 2,5

✅ Selected 2 transactions
```

### Quick Import (Skip Filtering)
```bash
# Import all transactions without filtering prompts
uv run --env-file .env python main.py --start-date 2024-01-01 --skip-filter
```

## Configuration Options

Environment variables you can set:

| Variable | Default | Description |
|----------|---------|-------------|
| `SPLITWISE_API_KEY` | *(required)* | Your Splitwise API key |
| `YNAB_ACCESS_TOKEN` | *(required)* | Your YNAB access token |
| `YNAB_ACCOUNT_NAME` | `Splitwise (Wallet)` | Target YNAB account name |
| `YNAB_API_URL` | `https://api.ynab.com/v1` | YNAB API endpoint |
| `SPLITWISE_API_URL` | `https://secure.splitwise.com/api/v3.0` | Splitwise API endpoint |

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test files
uv run pytest tests/test_processors/test_transaction_processor.py

# Run with verbose output
uv run pytest -v
```

### Code Quality

```bash
# Format code
uv run black src tests

# Sort imports
uv run isort src tests

# Lint code
uv run flake8 src tests

# Type checking
uv run mypy src
```

### Project Structure

```
ynab-splitwise/
├── src/ynab_splitwise/        # Main package
│   ├── auth/                  # Configuration and authentication
│   ├── clients/               # API clients (Splitwise, YNAB)
│   ├── processors/            # Data processing and transformation
│   ├── cli/                   # Command line interface
│   └── utils/                 # Utilities and exceptions
├── tests/                     # Test suite
├── main.py                    # Entry point
└── pyproject.toml             # Project configuration
```

## Troubleshooting

### Common Issues

1. **"Account not found" error**:
   - Ensure you have an account named "Splitwise (Wallet)" in YNAB
   - Or set `YNAB_ACCOUNT_NAME` to your preferred account name

2. **Authentication errors**:
   - Verify your API keys are correct and not expired
   - Check that environment variables are properly set

3. **No transactions found**:
   - Verify the start date is correct
   - Check that you have expenses in Splitwise for the date range
   - Ensure you're involved in the expenses (have a share)

4. **Duplicate transactions**:
   - The system automatically prevents duplicates using import IDs
   - If you see duplicates, they may be from manual imports

### Getting Help

1. Check the logs for detailed error messages
2. Run with `--verbose` for more debugging information
3. Check the source code for technical implementation details

## Security

- API keys are never logged or stored in plain text
- All network requests use HTTPS
- Transactions are created in "uncleared" status for your review

## License

This project is open source. See the license file for details.
