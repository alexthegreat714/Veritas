"""
Pytest Configuration and Fixtures for Veritas Tests

This module provides shared fixtures for testing the Veritas API.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Yields:
        TestClient: A test client instance for making requests.
    """
    with TestClient(app) as test_client:
        yield test_client
