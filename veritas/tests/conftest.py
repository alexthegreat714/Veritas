"""
Pytest Configuration and Fixtures for Veritas Tests

This module provides shared fixtures for testing the Veritas API.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils import reset_rate_state


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """
    Reset rate limiting state before each test.

    This ensures that rate limiting from one test doesn't affect others.
    """
    reset_rate_state()
    yield
    reset_rate_state()


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Yields:
        TestClient: A test client instance for making requests.
    """
    with TestClient(app) as test_client:
        yield test_client
