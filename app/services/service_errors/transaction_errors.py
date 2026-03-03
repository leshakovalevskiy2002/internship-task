from decimal import Decimal
from uuid import UUID


class TransactionServiceError(Exception):
    pass


class TransactionUserNotFoundError(TransactionServiceError):
    def __init__(self, user_id: UUID):
        super().__init__(f"User with id=`{user_id}` does not exist")


class TransactionUserBlockedError(TransactionServiceError):
    def __init__(self, user_id: UUID):
        super().__init__(f"User with id=`{user_id}` is blocked")


class UserBalanceNotFoundError(TransactionServiceError):
    def __init__(self, user_id: UUID, currency: str):
        super().__init__(f"Balance for user_id=`{user_id}` and currency=`{currency}` not found")


class NegativeBalanceError(TransactionServiceError):
    def __init__(self, new_balance: Decimal):
        super().__init__(f"Negative balance: {new_balance}")


class TransactionNotExistsError(TransactionServiceError):
    def __init__(self, transaction_id: UUID):
        super().__init__(f"Transaction with id=`{transaction_id}` does not exist")


class TransactionDoesNotBelongToUserException(TransactionServiceError):
    def __init__(self, transaction_id: UUID, user_id: UUID):
        super().__init__(f"Transaction with id=`{transaction_id}` does not belong to user with id=`{user_id}`")


class TransactionAlreadyRollbackedException(TransactionServiceError):
    def __init__(self, transaction_id: UUID):
        super().__init__(f"Transaction with id=`{transaction_id}` is already rollbacked")


class TransactionBlockedUserException(TransactionServiceError):
    def __init__(self, user_id: UUID):
        super().__init__(f"User with id=`{user_id}` is blocked")
