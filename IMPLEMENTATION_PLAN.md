# YNAB-Splitwise Integration Implementation Plan

## 📋 Project Overview
Automatically sync Splitwise expenses to YNAB "Splitwise (Wallet)" account, importing your owed share and money you get back with detailed transaction notes.

## 🎯 Requirements Summary

### User Requirements
- **Target Account**: "Splitwise (Wallet)" in YNAB
- **Data to Import**: All expenses (your owed share + money you get back)
- **Transaction Details**:
  - Payee: Expense description
  - Amount: Your owed share (negative) or money back (positive)
  - Memo: Detailed notes about paid amounts and users involved
- **Date Range**: CLI prompts user for start date
- **Categories**: No mapping, let YNAB auto-suggest based on description
- **Currency**: Same currency, no conversion needed
- **Error Handling**: Script stops on errors with detailed logging
- **Testing**: Comprehensive unit tests required

### Technical Requirements
- **Splitwise API**: Use API key authentication
- **YNAB SDK**: Use Python SDK with Bearer token
- **Duplicate Prevention**: Use YNAB's import_id system
- **CLI Interface**: User-friendly command line interface
- **Logging**: Detailed error messages and progress tracking

## 🏗️ Architecture Design

### Core Components
1. **Authentication Handler** - Manage API keys and tokens
2. **Splitwise Client** - Fetch and parse expense data
3. **YNAB Client** - Create transactions and manage accounts
4. **Transaction Processor** - Transform data between systems
5. **Duplicate Detector** - Prevent duplicate imports
6. **CLI Interface** - User interaction and configuration
7. **Error Handler** - Robust error management
8. **Test Suite** - Comprehensive unit testing

### Data Flow
```
User Input (Date) → Splitwise API → Data Processing → YNAB API → Success/Error
```

## 📁 Project Structure
```
ynab-splitwise/
├── src/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── splitwise.py
│   │   └── ynab.py
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── transaction_processor.py
│   │   └── duplicate_detector.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── interface.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── exceptions.py
├── tests/
│   ├── __init__.py
│   ├── test_auth/
│   ├── test_clients/
│   ├── test_processors/
│   ├── test_cli/
│   └── fixtures/
├── main.py
├── requirements.txt
├── pytest.ini
└── README.md
```

## 🔐 Authentication Design

### Environment Variables
- `SPLITWISE_API_KEY`: Your Splitwise API key
- `YNAB_ACCESS_TOKEN`: Your YNAB Bearer token

### Security Features
- No tokens logged or stored in plain text
- Environment variable validation
- Secure token handling

## 🔄 Data Processing Logic

### Import ID Format
```python
import_id = f"splitwise_{expense_id}"
```

### Transaction Transformation
```python
# For money you owe (negative amount)
amount = -abs(your_owed_share)

# For money you get back (positive amount)
amount = abs(your_received_share)

# Memo format
memo = f"Paid: ${total_paid}, Owed: ${your_owed}, Users: {user_list}"
```

### Duplicate Detection Strategy
1. **Primary**: Use YNAB `import_id` with format `splitwise_{expense_id}`
2. **Fallback**: Match by amount, date, and memo content
3. **Metadata**: Store Splitwise expense ID in transaction memo
4. **Sync State**: Track processing to avoid reprocessing

## 📊 Implementation Phases

### Phase 1: Core Infrastructure (High Priority)
1. **Set up project structure and dependencies**
   - Create directory structure
   - Install required packages (ynab-sdk-python, requests, pytest)
   - Set up basic configuration

2. **Create authentication and configuration handlers**
   - Environment variable management
   - API key validation
   - Configuration file support

3. **Implement Splitwise API client**
   - API key authentication
   - Expense fetching with date filtering
   - Error handling for API responses

4. **Create YNAB client**
   - Bearer token authentication
   - Account lookup by name
   - Transaction creation with import_id

5. **Build duplicate detection system**
   - Import ID generation
   - Existing transaction checking
   - Fallback matching logic

### Phase 2: Data Processing (Medium Priority)
6. **Implement transaction transformation logic**
   - Amount calculation (owed vs received)
   - Memo generation with details
   - Date format conversion

7. **Create CLI interface**
   - User input for start date
   - Progress feedback
   - Configuration options

8. **Write comprehensive unit tests**
   - Test all components in isolation
   - Mock external API calls
   - Edge case coverage

### Phase 3: Polish & Integration (Low Priority)
9. **Add error handling and logging**
   - Detailed error messages
   - Progress logging
   - Failure recovery options

10. **Test end-to-end integration**
    - Full workflow testing
    - Error scenario testing
    - Performance validation

## 🧪 Testing Strategy

### Unit Tests
- **Authentication**: Token validation, configuration loading
- **Splitwise Client**: API responses, data parsing, error handling
- **YNAB Client**: Account lookup, transaction creation, import_id handling
- **Transaction Processor**: Amount calculations, memo generation
- **Duplicate Detector**: Import ID matching, fallback logic
- **CLI Interface**: User input handling, date validation

### Test Coverage Goals
- Minimum 90% code coverage
- All error paths tested
- Edge cases covered
- API mocking for external dependencies

### Test Data
- Sample Splitwise expense responses
- Mock YNAB account and transaction data
- Various date formats and edge cases
- Error response scenarios

## 🚨 Error Handling Strategy

### Error Types
1. **Authentication Errors**: Invalid API keys, expired tokens
2. **Network Errors**: API timeouts, connection issues
3. **Data Errors**: Invalid dates, malformed responses
4. **Business Logic Errors**: Account not found, duplicate detection failures

### Error Response
- **Fail Fast**: Stop execution on critical errors
- **Detailed Logging**: Context-rich error messages
- **User Feedback**: Clear error explanations
- **Recovery Suggestions**: Actionable next steps

## 🔧 Configuration Options

### CLI Arguments
- `--start-date`: Date to begin syncing from (YYYY-MM-DD)
- `--dry-run`: Preview transactions without importing
- `--verbose`: Detailed logging output
- `--config`: Custom configuration file path

### Configuration File (Optional)
```json
{
  "ynab_account_name": "Splitwise (Wallet)",
  "default_start_date": "2024-01-01",
  "log_level": "INFO",
  "batch_size": 50
}
```

## 📈 Success Metrics

### Completion Criteria
- [ ] All Splitwise expenses imported correctly
- [ ] No duplicate transactions created
- [ ] Proper amount calculations (owed vs received)
- [ ] Detailed memos with transaction context
- [ ] Robust error handling and logging
- [ ] 90%+ unit test coverage
- [ ] Clean, maintainable code structure

### Performance Targets
- Handle 1000+ transactions efficiently
- Complete sync in under 2 minutes
- Graceful handling of API rate limits
- Memory-efficient processing

## 🚀 Future Enhancements

### Potential Features
- **Scheduling**: Automated daily/weekly syncs
- **Category Mapping**: Custom Splitwise to YNAB category mapping
- **Multi-Currency**: Currency conversion support
- **Sync History**: Track sync operations and rollback capability
- **Web Interface**: Optional web UI for configuration
- **Notifications**: Email/SMS alerts for sync completion

### Extensibility
- Plugin architecture for custom processors
- Configuration-driven business rules
- API for integration with other tools
- Database backend for sync history

---

## 📝 Notes

### Implementation Order
1. Start with core infrastructure (authentication, API clients)
2. Build data processing pipeline
3. Add CLI interface and user experience
4. Implement comprehensive testing
5. Polish error handling and logging

### Development Principles
- **Test-Driven Development**: Write tests before implementation
- **Clean Code**: Readable, maintainable, well-documented
- **Error-First**: Robust error handling from the start
- **User-Centric**: Focus on user experience and feedback
- **Security-Aware**: Protect sensitive data and credentials

### Key Decisions
- Use YNAB's import_id system for duplicate prevention
- Fail fast on errors with detailed context
- CLI-first interface with future extensibility
- Comprehensive unit testing for reliability
- Environment variables for secure credential management
