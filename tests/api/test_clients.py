import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from httpx import AsyncClient
from uuid import UUID, uuid4
from app.models.schemas import Client, ClientUser, User, UserRole, SubscriptionStatus

# Mock user for testing
TEST_USER = User(
    id=uuid4(),
    email="test@example.com",
    created_at="2024-03-17T00:00:00Z"
)

# Mock client for testing
TEST_CLIENT = Client(
    id=uuid4(),
    name="Test Church",
    subscription_status=SubscriptionStatus.trial,
    created_at="2024-03-17T00:00:00Z",
    created_by=TEST_USER.id,
    updated_at="2024-03-17T00:00:00Z",
    updated_by=TEST_USER.id
)

# Mock client user for testing
TEST_CLIENT_USER = ClientUser(
    client_id=TEST_CLIENT.id,
    user_id=TEST_USER.id,
    role=UserRole.owner,
    created_at="2024-03-17T00:00:00Z",
    created_by=TEST_USER.id,
    updated_at="2024-03-17T00:00:00Z",
    updated_by=TEST_USER.id
)

@pytest.fixture
def mock_supabase_service():
    """Mock the Supabase service"""
    with patch("app.api.endpoints.clients.supabase_service") as mock:
        mock.get_user_client = AsyncMock(return_value=TEST_CLIENT)
        mock.create_client = AsyncMock(return_value=TEST_CLIENT)
        mock.get_client_users = AsyncMock(return_value=[TEST_CLIENT_USER])
        mock.add_client_user = AsyncMock(return_value=TEST_CLIENT_USER)
        mock.remove_client_user = AsyncMock(return_value=None)
        yield mock

@pytest.fixture
def mock_get_current_user():
    """Mock the get_current_user dependency"""
    with patch("app.api.endpoints.clients.get_current_user") as mock:
        mock.return_value = TEST_USER
        yield mock

@pytest.mark.asyncio
async def test_get_current_client(
    client: AsyncClient,
    mock_supabase_service,
    mock_get_current_user
):
    """Test getting current client information"""
    response = await client.get("/api/v1/clients/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(TEST_CLIENT.id)
    assert data["name"] == TEST_CLIENT.name
    mock_supabase_service.get_user_client.assert_called_once_with(TEST_USER.id)

@pytest.mark.asyncio
async def test_create_client(
    client: AsyncClient,
    mock_supabase_service,
    mock_get_current_user
):
    """Test creating a new client"""
    response = await client.post("/api/v1/clients/", params={"name": "New Church"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == TEST_CLIENT.name
    mock_supabase_service.create_client.assert_called_once_with("New Church", TEST_USER.id)

@pytest.mark.asyncio
async def test_list_client_users(
    client: AsyncClient,
    mock_supabase_service,
    mock_get_current_user
):
    """Test listing client users"""
    response = await client.get("/api/v1/clients/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == str(TEST_USER.id)
    mock_supabase_service.get_client_users.assert_called_once_with(TEST_USER.id)

@pytest.mark.asyncio
async def test_add_client_user(
    client: AsyncClient,
    mock_supabase_service,
    mock_get_current_user
):
    """Test adding a user to client"""
    response = await client.post(
        "/api/v1/clients/users",
        params={"email": "new@example.com", "role": "member"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "owner"  # From our mock data
    mock_supabase_service.add_client_user.assert_called_once_with(
        email="new@example.com",
        role="member",
        added_by=TEST_USER.id
    )

@pytest.mark.asyncio
async def test_add_client_user_already_in_client(
    client: AsyncClient,
    mock_supabase_service,
    mock_get_current_user
):
    """Test adding a user that already belongs to a client"""
    mock_supabase_service.add_client_user.side_effect = Exception(
        "User already belongs to client: Another Church"
    )
    response = await client.post(
        "/api/v1/clients/users",
        params={"email": "existing@example.com", "role": "member"}
    )
    assert response.status_code == 500
    data = response.json()
    assert "already belongs to client" in data["detail"]

@pytest.mark.asyncio
async def test_remove_client_user(
    client: AsyncClient,
    mock_supabase_service,
    mock_get_current_user
):
    """Test removing a user from client"""
    user_id = uuid4()
    response = await client.delete(f"/api/v1/clients/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    mock_supabase_service.remove_client_user.assert_called_once_with(
        user_id=user_id,
        removed_by=TEST_USER.id
    ) 