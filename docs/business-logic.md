# Business Logic

## Users

- On registration, a user is created with status `ACTIVE`
- Balances are initialized for all supported currencies
- Supported currencies: `USD`, `EUR`, `BTC`, `ETH`, `DOGE`, `USDT`, `AUD`, `CAD`, `ARS`, `PLN`
- User statuses: `ACTIVE`, `BLOCKED`
- Blocked users cannot create transactions or roll back existing ones;
  such requests return `400 blocked_user`

## Transactions

Supported types: `DEPOSIT`, `WITHDRAW`, `REVERSAL`

### DEPOSIT

`balance = balance + amount`

### WITHDRAW

`balance = balance - amount`

The balance must never become negative. A withdrawal that would result in a
negative balance is rejected with `400 negative_balance_after_operation`.

### REVERSAL

`REVERSAL` is never created directly. It is created automatically when an
existing transaction is rolled back.

- For a `DEPOSIT`, the amount is subtracted from the balance.
- For a `WITHDRAW`, the amount is added back to the balance.

The reversal transaction references the original one via `reversal_of_id`.
A transaction can only be rolled back once; a second attempt returns
`400 transaction_already_reversed`.

## Analytics

The service generates an analytics report for the last **52 completed weeks**.
The current incomplete week is excluded. Generation is asynchronous; the
result is cached in Redis.

```text
             GET /reports/analysis
                       │
                       ▼
                Check Redis
                  /       \
                 /         \
             exists       missing
               │              │
               ▼              ▼
         Return report    Acquire lock
                              │
                              ▼
                       Generate report
                              │
                              ▼
                         Save to Redis
```

If a report is already cached, it is returned immediately. Otherwise,
generation is started in the background and the endpoint returns a
generation status.