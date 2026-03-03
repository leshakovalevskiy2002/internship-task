class UserServiceError(Exception):
    pass


class UserAlreadyExistsError(UserServiceError):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email=`{email}` already exists")


class UserNotFoundError(UserServiceError):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with id=`{user_id}` does not exist")


class UserAlreadyBlockedError(UserServiceError):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with id=`{user_id}` is already blocked")


class UserAlreadyActiveError(UserServiceError):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with id=`{user_id}` is already active")
