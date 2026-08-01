import uuid
from decimal import Decimal

from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import CurrencyEnum, UserStatusEnum
from app.models.user import User

prefix = "/api/v1/users"


class TestRegistrationAPI:
    async def test_registration_success(self, client: AsyncClient, session: AsyncSession):
        response = await client.post(f"{prefix}/registration", json={"email": "test@example.com"})

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["email"] == "test@example.com"
        assert data["status"] == UserStatusEnum.ACTIVE

        user = await session.scalar(
            select(User).options(selectinload(User.user_balances)).where(User.email == data["email"])
        )

        assert user is not None
        assert user.email == data["email"]

        assert len(user.user_balances) == len(CurrencyEnum)

    async def test_registration_duplicate_email(self, client: AsyncClient):
        r1 = await client.post(f"{prefix}/registration", json={"email": "test@example.com"})
        assert r1.status_code == status.HTTP_201_CREATED

        r2 = await client.post(f"{prefix}/registration", json={"email": "test@example.com"})
        assert r2.status_code == status.HTTP_409_CONFLICT

    async def test_registration_invalid_email(self, client: AsyncClient):
        r1 = await client.post(f"{prefix}/registration", json={"email": "wrong"})
        assert r1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetUsersWithBalances:
    async def test_get_users_returns_all(self, client: AsyncClient):
        response = await client.get(f"{prefix}")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_users_filters_by_id(self, client, user_factory):
        user = await user_factory()
        response = await client.get(f"{prefix}", params={"id": user.id})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(user.id)

    async def test_get_users_filters_by_email(self, client, user_factory):
        user = await user_factory()
        response = await client.get(f"{prefix}", params={"email": user.email})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == user.email

    async def test_get_users_returns_balances(self, client, user_factory_with_balances):
        user = await user_factory_with_balances()
        response = await client.get(f"{prefix}", params={"id": user.id})

        data = response.json()[0]

        assert "balances" in data
        assert isinstance(data["balances"], list)

        balance = data["balances"][0]

        assert "currency" in balance
        assert "amount" in balance

    async def test_get_users_returns_sorted_balances(self, client, user_factory_with_balances):
        user = await user_factory_with_balances(generate_random_balances=True)
        response = await client.get(f"{prefix}", params={"id": user.id})

        balances = response.json()[0]["balances"]

        amounts = [Decimal(balance["amount"]) for balance in balances]
        assert amounts == sorted(amounts)


class TestChangeUserStatus:
    async def test_change_user_status_success(self, client, user_for_api):
        user = await user_for_api()
        user_uuid = user.id

        response = await client.patch(f"{prefix}/{user_uuid}", json={"status": UserStatusEnum.BLOCKED})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == UserStatusEnum.BLOCKED
        assert data["email"] == user.email

    async def test_change_user_status_user_not_found(self, client, user_for_api):
        _ = await user_for_api()
        not_existing_uuid = uuid.uuid4()

        response = await client.patch(f"{prefix}/{not_existing_uuid}", json={"status": UserStatusEnum.BLOCKED})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    async def test_change_user_status_user_already_active(self, client, user_for_api):
        user = await user_for_api()
        user_uuid = user.id

        response = await client.patch(f"{prefix}/{user_uuid}", json={"status": UserStatusEnum.ACTIVE})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()

    async def test_change_user_status_user_already_blocked(self, client, user_for_api):
        user = await user_for_api(status=UserStatusEnum.BLOCKED)
        user_uuid = user.id

        response = await client.patch(f"{prefix}/{user_uuid}", json={"status": UserStatusEnum.BLOCKED})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()
