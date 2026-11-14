A comprehensive multi-currency financial platform for user management and transaction processing.

## Core Features

### User Management
- User registration with automatic balance creation for all supported currencies
- User listing with filtering (ID, email, status)
- Status management (ACTIVE/BLOCKED)

### Financial Operations
- **Deposits** — add funds to user balance
- **Withdrawals** — deduct funds (rejected if balance insufficient)
- **Transaction rollback** — automatic reversal creation
- **Transaction history** — filtered by user, newest first

### Multi-Currency Support
USD, EUR, BTC, ETH, DOGE, USDT, AUD, CAD, ARS, PLN — each user gets a balance for every currency automatically.

### Analytics & Reporting
Asynchronous report generation for the last 52 weeks, with Redis caching and a lock mechanism to prevent duplicate generation.

## Security & Validation
- Email validation
- Balance sufficiency checks
- Blocked users cannot perform transactions
- No direct REVERSAL creation (only via rollback)
- Prevention of duplicate rollbacks

## Workflow
1. **Register** → user created with all currency balances
2. **Transaction** → balance updated (DEPOSIT adds, WITHDRAW subtracts)
3. **Rollback** → creates REVERSAL transaction compensating the original
4. **Report** → generated async, cached for performance
