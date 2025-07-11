"""Sample data for testing."""

from datetime import datetime

# Sample Splitwise user data
SAMPLE_USER = {
    "id": 12345,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "registration_status": "confirmed",
}

# Sample Splitwise expense data
SAMPLE_EXPENSE = {
    "id": 67890,
    "cost": "25.00",
    "description": "Grocery Shopping",
    "details": "Weekly groceries from the supermarket",
    "date": "2024-01-15T10:30:00Z",
    "currency_code": "USD",
    "category_id": 15,
    "group_id": 391,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "users": [
        {
            "user": {"id": 12345, "first_name": "John", "last_name": "Doe"},
            "user_id": 12345,
            "paid_share": "25.00",
            "owed_share": "12.50",
        },
        {
            "user": {"id": 54321, "first_name": "Jane", "last_name": "Smith"},
            "user_id": 54321,
            "paid_share": "0.00",
            "owed_share": "12.50",
        },
    ],
}

# Sample expense where user owes money
SAMPLE_EXPENSE_OWED = {
    "id": 11111,
    "cost": "30.00",
    "description": "Restaurant Dinner",
    "details": "Nice Italian restaurant",
    "date": "2024-01-20T19:00:00Z",
    "currency_code": "USD",
    "users": [
        {
            "user": {"id": 12345, "first_name": "John", "last_name": "Doe"},
            "user_id": 12345,
            "paid_share": "0.00",
            "owed_share": "15.00",
        },
        {
            "user": {"id": 54321, "first_name": "Jane", "last_name": "Smith"},
            "user_id": 54321,
            "paid_share": "30.00",
            "owed_share": "15.00",
        },
    ],
}

# Sample expense where user gets money back
SAMPLE_EXPENSE_GETS_BACK = {
    "id": 22222,
    "cost": "40.00",
    "description": "Gas Station",
    "details": "Filled up the car",
    "date": "2024-01-25T14:00:00Z",
    "currency_code": "USD",
    "users": [
        {
            "user": {"id": 12345, "first_name": "John", "last_name": "Doe"},
            "user_id": 12345,
            "paid_share": "40.00",
            "owed_share": "20.00",
        },
        {
            "user": {"id": 54321, "first_name": "Jane", "last_name": "Smith"},
            "user_id": 54321,
            "paid_share": "0.00",
            "owed_share": "20.00",
        },
    ],
}

# Sample expense where user is not involved
SAMPLE_EXPENSE_NOT_INVOLVED = {
    "id": 33333,
    "cost": "15.00",
    "description": "Coffee Meeting",
    "date": "2024-01-30T09:00:00Z",
    "currency_code": "USD",
    "users": [
        {
            "user": {"id": 54321, "first_name": "Jane", "last_name": "Smith"},
            "user_id": 54321,
            "paid_share": "15.00",
            "owed_share": "7.50",
        },
        {
            "user": {"id": 99999, "first_name": "Bob", "last_name": "Wilson"},
            "user_id": 99999,
            "paid_share": "0.00",
            "owed_share": "7.50",
        },
    ],
}

# Sample YNAB transaction data
SAMPLE_YNAB_TRANSACTION = {
    "id": "ynab-txn-123",
    "amount": 12500,  # $12.50 in milliunits
    "payee_name": "Grocery Shopping",
    "memo": "Paid: $25.00, Owed: $12.50 | Users: John Doe, Jane Smith | Splitwise ID: 67890",
    "date": datetime(2024, 1, 15).date(),
    "import_id": "splitwise_67890",
}

# Sample API responses
SPLITWISE_GET_CURRENT_USER_RESPONSE = {"user": SAMPLE_USER}

SPLITWISE_GET_EXPENSES_RESPONSE = {
    "expenses": [SAMPLE_EXPENSE, SAMPLE_EXPENSE_OWED, SAMPLE_EXPENSE_GETS_BACK]
}

YNAB_ACCOUNTS_RESPONSE = {
    "data": {
        "accounts": [
            {
                "id": "account-123",
                "name": "Splitwise (Wallet)",
                "type": "cash",
                "balance": 100000,
            },
            {
                "id": "account-456",
                "name": "Checking Account",
                "type": "checking",
                "balance": 500000,
            },
        ]
    }
}

YNAB_CREATE_TRANSACTION_RESPONSE = {
    "data": {
        "transaction": {
            "id": "txn-123",
            "amount": -15000,
            "payee_name": "Restaurant Dinner",
            "memo": "Test memo",
            "date": datetime(2024, 1, 20).date(),
            "import_id": "splitwise_11111",
        }
    }
}
