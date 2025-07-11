# YNAB-Splitwise Integration - Development Guide

## Project Overview

This is a Python CLI tool that automatically syncs Splitwise expenses to YNAB (You Need A Budget), importing each user's share of expenses as individual transactions. The tool handles complex expense splitting calculations, duplicate detection, and provides a user-friendly interface for transaction filtering.

### Core Architecture
- **CLI Interface**: Click-based command line with filtering options
- **API Clients**: Separate clients for Splitwise and YNAB APIs
- **Transaction Processing**: Sophisticated expense-to-transaction conversion
- **Duplicate Detection**: Import ID-based deduplication system
- **Error Handling**: Comprehensive exception handling with detailed logging

## Key Development Context

### Package Manager & Environment
- **Use `uv` for all Python operations** (not pip/poetry)
- Run commands: `uv run --env-file .env python main.py`
- Install deps: `uv sync` or `uv sync --all-extras` for dev
- Environment variables loaded from `.env` file

### Pre-commit Hooks (CRITICAL)
- **All commits must pass pre-commit hooks**
- Configured: black, isort, flake8, trailing whitespace, end-of-file fixes
- Auto-installed on clone: `uv run pre-commit install`
- Manual run: `uv run pre-commit run --all-files`

### Commit Message Format
- Use emoji prefix: `🐛 Fix transaction date bug`
- Keep first line under 50 chars
- Include Claude signature for AI-assisted commits

## Critical API Issues & Solutions

### YNAB SDK Date Attribute Bug (FIXED)
**Problem**: `'TransactionDetail' object has no attribute 'date'`
**Solution**: Use `txn.var_date` instead of `txn.date` in response handling
**Location**: `src/ynab_splitwise/clients/ynab_client.py:187, 253`

### YNAB Transaction Types (FIXED)
**Problem**: Pydantic validation errors with SaveTransactionWithOptionalFields
**Solution**: Always use `NewTransaction` for creating transactions
**Location**: Import from `ynab` module, used in transaction creation

### Splitwise Date Filtering
**Important**: `dated_after` and `dated_before` are inclusive
**Usage**: `dated_after="2024-01-01"` includes transactions on Jan 1st

## Development Workflow

### Environment Setup
```bash
# Required environment variables in .env
SPLITWISE_API_KEY=your_splitwise_api_key_here
YNAB_ACCESS_TOKEN=your_ynab_access_token_here

# Optional (with defaults)
YNAB_ACCOUNT_NAME=Splitwise (Wallet)
YNAB_API_URL=https://api.ynab.com/v1
SPLITWISE_API_URL=https://secure.splitwise.com/api/v3.0
```

### Testing & Quality
```bash
# Run tests
uv run pytest
uv run pytest --cov=src  # with coverage

# Code quality (required before commit)
uv run black src tests
uv run isort src tests
uv run flake8 src tests
uv run mypy src
```

### Running the Application
```bash
# Interactive mode
uv run --env-file .env python main.py

# With specific date
uv run --env-file .env python main.py --start-date 2024-01-01

# Preview only (no import)
uv run --env-file .env python main.py --dry-run --start-date 2024-01-01

# Skip filtering (import all)
uv run --env-file .env python main.py --skip-filter
```

## Key Technical Patterns

### Transaction Processing Flow
1. Fetch Splitwise expenses with pagination
2. Calculate user's share (paid - owed = net amount)
3. Convert to YNAB format with detailed memos
4. Detect duplicates using import IDs (`splitwise_{expense_id}`)
5. Filter transactions by user selection
6. Batch import to YNAB with error handling

### Amount Calculation Logic
- **Positive amounts**: Money you get back (paid > owed)
- **Negative amounts**: Money you owe (paid < owed)
- **Milliunits**: YNAB uses milliunits (multiply by 1000)

### Error Handling Strategy
- Custom exception hierarchy in `utils/exceptions.py`
- Graceful degradation with user-friendly messages
- Detailed logging for debugging
- API rate limiting and retry logic

## Common Development Issues

### README.md Binary Corruption
**Problem**: File shows as binary, not rendering on GitHub
**Solution**: Recreate as clean UTF-8 text file
**Cause**: Hidden binary characters from formatting tools

### Transaction Filtering UI
- Position-based filtering (not date-based)
- Inclusive ranges (position 1-5 includes both 1 and 5)
- Clear user prompts explaining inclusive behavior

### CLI Display Issues
- Use actual `\n` not escaped `\\n` in click.echo()
- Sort transactions chronologically (oldest first) for display
- Format amounts with proper +/- signs

## API Integration Notes

### Context7 MCP Usage
- Use for Splitwise API documentation: `mcp__context7__resolve-library-id`
- Use for YNAB Python SDK help: `/ynab/ynab-sdk-python`
- Essential for understanding API response structures

### YNAB Account Requirements
- Must have account named "Splitwise (Wallet)" (or configure custom name)
- Transactions created in "uncleared" status for user review
- Import IDs prevent duplicates across multiple runs

### Splitwise API Pagination
- Use limit=100 for efficiency
- Handle offset-based pagination
- Filter by `dated_after` for incremental syncs

## Testing Strategy

### Test Coverage
- Unit tests for all processors and utilities
- Integration tests for API clients (mocked)
- CLI interface testing with Click testing utilities
- 44 tests total with high coverage

### Key Test Areas
- Amount calculation logic
- Duplicate detection algorithms
- Date filtering and parsing
- Error handling scenarios
- Transaction formatting

## Project Structure

```
src/ynab_splitwise/
├── auth/           # Config and environment loading
├── clients/        # API clients (Splitwise, YNAB)
├── processors/     # Business logic and data transformation
├── cli/           # Command line interface
└── utils/         # Exceptions, logging, helpers

tests/             # Comprehensive test suite
main.py           # Application entry point
```

## Deployment Notes

### Dependencies
- Python 3.8+ required
- Key dependencies: ynab-sdk-python, requests, click, python-dateutil
- Development tools: black, isort, flake8, mypy, pytest, pre-commit

### Security Considerations
- API keys never logged or stored in code
- Environment variable-based configuration
- HTTPS for all API communications
- Transactions require manual approval in YNAB

---

**Remember**: This is a financial integration tool. Always test thoroughly with dry-runs before importing real transactions. Keep API credentials secure and never commit them to version control.
