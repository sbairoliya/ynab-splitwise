# 💰 YNAB-Splitwise Integration

> 🚀 **Automatically sync your Splitwise expenses to YNAB in just 3 steps!**

Never manually enter shared expenses again! This tool imports your share of Splitwise expenses directly into YNAB with detailed transaction notes.

## 🎯 Quick Start

### 📋 What You Need
- 🐍 Python 3.8+
- 💳 YNAB account with API access
- 👥 Splitwise account with API access
- 🏦 YNAB account named "Splitwise (Wallet)"

### ⚡ Get Started in 3 Steps

#### 1️⃣ **Install & Setup**
```bash
# Clone and install
git clone <repository-url>
cd ynab-splitwise
uv sync

# Copy environment template
cp .env.example .env
```

#### 2️⃣ **Get API Keys**
- 🔑 **Splitwise**: Visit [Splitwise Apps](https://secure.splitwise.com/apps) → Create New App
- 🔑 **YNAB**: Visit [YNAB Developer Settings](https://app.ynab.com/settings/developer) → New Token

#### 3️⃣ **Run the Sync**
```bash
# Add your API keys to .env file, then:
uv run --env-file .env python main.py
```

That's it! 🎉 Follow the prompts to import your expenses.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💸 **Smart Amount Calculation** | Imports exactly what you owe or get back |
| 📝 **Detailed Memos** | Shows who paid, amounts, and expense details |
| 🚫 **Duplicate Prevention** | Never import the same expense twice |
| 🎛️ **Transaction Filtering** | Choose which expenses to import |
| 📅 **Date Range Selection** | Sync from any start date |
| 🔍 **Preview Mode** | See what will be imported before committing |

## 💻 Usage Examples

```bash
# 🔍 Preview transactions without importing
uv run --env-file .env python main.py --dry-run --start-date 2024-01-01

# ⚡ Import all transactions (skip filtering)
uv run --env-file .env python main.py --skip-filter --start-date 2024-01-01

# 📊 Enable detailed logging
uv run --env-file .env python main.py --verbose
```

## 🔧 CLI Options

| Option | Description |
|--------|-------------|
| `--start-date` | 📅 Start date for syncing (YYYY-MM-DD) |
| `--dry-run` | 🔍 Preview without importing |
| `--verbose` | 📊 Enable detailed logging |
| `--skip-filter` | ⚡ Import all found transactions |
| `--help` | ❓ Show help message |

## 🎮 Interactive Filtering

After finding your expenses, choose what to import:

```
📋 Transaction Preview:
--------------------------------------------------------------------------------
 1. 2024-01-15 |    -$12.50 | Weekly groceries
 2. 2024-01-18 |    +$25.00 | Dinner split refund
 3. 2024-01-20 |    -$8.75  | Coffee meeting
 4. 2024-01-22 |    -$45.00 | Uber ride home
 5. 2024-01-25 |    +$15.50 | Movie tickets refund

🔢 How would you like to filter?
1. ✅ Import all transactions
2. ⬆️ Import up to position # (e.g., 1-5)
3. ⬇️ Import from position # onwards (e.g., 3-5)
4. 🎯 Import specific range (e.g., 2-4)
5. 🎲 Import specific numbers (e.g., 1,3,5)
6. ❌ Cancel import
```

## 🏗️ How It Works

1. 📥 **Fetch** your Splitwise expenses since the start date
2. 🧮 **Calculate** your share (what you owe vs. get back)
3. 🔄 **Convert** to YNAB format with detailed memos
4. 🔍 **Check** for duplicates using import IDs
5. 💾 **Import** to your YNAB "Splitwise (Wallet)" account

## 📊 Transaction Details

Each imported transaction includes:

- 💰 **Amount**: Your net share (- for owed, + for refunds)
- 🏪 **Payee**: Expense description from Splitwise
- 📝 **Memo**: Detailed breakdown with:
  - 💳 Amount you paid and owed
  - 👥 Users involved in the expense
  - 📋 Original expense notes
  - 🆔 Splitwise expense ID

## ⚙️ Configuration

### 🔐 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SPLITWISE_API_KEY` | *(required)* | 🔑 Your Splitwise API key |
| `YNAB_ACCESS_TOKEN` | *(required)* | 🔑 Your YNAB access token |
| `YNAB_ACCOUNT_NAME` | `Splitwise (Wallet)` | 🏦 Target YNAB account |
| `YNAB_API_URL` | `https://api.ynab.com/v1` | 🌐 YNAB API endpoint |
| `SPLITWISE_API_URL` | `https://secure.splitwise.com/api/v3.0` | 🌐 Splitwise API endpoint |

### 📁 .env File Example
```bash
SPLITWISE_API_KEY=your_splitwise_api_key_here
YNAB_ACCESS_TOKEN=your_ynab_access_token_here
YNAB_ACCOUNT_NAME=Splitwise (Wallet)
```

## 🛠️ Development

### 🧪 Running Tests
```bash
uv run pytest                    # Run all tests
uv run pytest --cov=src        # With coverage
uv run pytest -v               # Verbose output
```

### 🎨 Code Quality
```bash
uv run black src tests         # Format code
uv run isort src tests         # Sort imports
uv run flake8 src tests        # Lint code
uv run mypy src                # Type checking
```

## 🆘 Troubleshooting

### 🔧 Common Issues

**❌ "Account not found" error**
- ✅ Create an account named "Splitwise (Wallet)" in YNAB
- ✅ Or set `YNAB_ACCOUNT_NAME` to your preferred account

**❌ Authentication errors**
- ✅ Verify API keys are correct and not expired
- ✅ Check environment variables are properly set

**❌ No transactions found**
- ✅ Verify start date is correct
- ✅ Check you have expenses in Splitwise for that date range
- ✅ Ensure you're involved in the expenses (have a share)

**❌ Duplicate transactions**
- ✅ System automatically prevents duplicates using import IDs
- ✅ If you see duplicates, they may be from manual imports

### 📞 Getting Help
1. 📋 Check logs for detailed error messages
2. 🔍 Run with `--verbose` for debugging info
3. 💻 Check source code for technical details

## 🔒 Security

- 🔐 API keys never logged or stored in code
- 🔒 All requests use HTTPS encryption
- ✅ Transactions created in "uncleared" status for your review

## 📦 Installation Requirements

- 🐍 **Python**: 3.8 or higher
- 📚 **Key Dependencies**: ynab-sdk-python, requests, click
- 🛠️ **Package Manager**: uv (recommended) or pip

## 📜 License

This project is open source. See the license file for details.

---

💡 **Pro Tip**: Always test with `--dry-run` first to see what will be imported before making actual changes to your YNAB budget!
