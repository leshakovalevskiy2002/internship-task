import pytest
from pydantic import ValidationError

from app.schemas.users import UserRegistrationRequest


class TestUserRegistrationRequest:
    @pytest.mark.parametrize(
        ["email", "expected"],
        [
            ("test@test.com", "test@test.com"),
            ("  test@test.com ", "test@test.com"),
            (" test @test. com ", "test@test.com"),
            ("\ttest @test.com\n ", "test@test.com"),
        ],
    )
    def test_email_normalization(self, email, expected):
        model = UserRegistrationRequest(email=email)
        assert model.email == expected

    def test_email_only_spaces(self):
        with pytest.raises(ValidationError):
            UserRegistrationRequest(email="     ")
