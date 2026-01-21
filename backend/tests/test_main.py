import pytest
import asyncio
from httpx import AsyncClient
from main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok", 
        "message": "Smart Email Advisor API is running"
    }

@pytest.mark.asyncio
async def test_email_analysis(client: AsyncClient):
    """Test email analysis endpoint"""
    # Mock email data
    email_data = {
        "subject": "Важлива зустріч завтра",
        "content": "Привіт! Нагадую про нашу зустріч завтра о 14:00 в офісі. Будь ласка, підтверди участь.",
        "sender": "colleague@company.com",
        "recipient": "user@company.com"
    }
    
    # For now, this will fail due to authentication
    # In a real test, we would need to get a valid token first
    response = await client.post("/api/emails/analyze", json=email_data)
    # Expecting 403 because no auth token
    assert response.status_code in [401, 403]

@pytest.mark.asyncio 
async def test_login_endpoint(client: AsyncClient):
    """Test user login"""
    login_data = {
        "email": "test@example.com",
        "password": "testpass"
    }
    
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "test@example.com"