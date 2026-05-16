"""
Integration Tests - API and service integration
These run on Azure AKS for scalability
"""

import pytest
import requests
from unittest.mock import Mock


class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def api_client(self):
        """Fixture to create API client"""
        return requests.Session()
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API"""
        return "https://api.example.com"
    
    def test_user_crud_workflow(self, api_client, base_url):
        """Test complete user CRUD workflow"""
        
        # Create user
        response = api_client.post(
            f"{base_url}/api/users",
            json={
                "name": "Integration Test User",
                "email": "integration@test.com",
                "age": 30
            }
        )
        assert response.status_code == 201
        user_id = response.json()['id']
        
        # Read user
        response = api_client.get(f"{base_url}/api/users/{user_id}")
        assert response.status_code == 200
        assert response.json()['email'] == "integration@test.com"
        
        # Update user
        response = api_client.put(
            f"{base_url}/api/users/{user_id}",
            json={"age": 31}
        )
        assert response.status_code in [200, 204]
        
        # Verify update
        response = api_client.get(f"{base_url}/api/users/{user_id}")
        assert response.json()['age'] == 31
        
        # Delete user
        response = api_client.delete(f"{base_url}/api/users/{user_id}")
        assert response.status_code in [200, 204]
        
        # Verify deletion
        response = api_client.get(f"{base_url}/api/users/{user_id}")
        assert response.status_code == 404
    
    def test_authentication_flow(self, api_client, base_url):
        """Test authentication flow"""
        
        # Login
        response = api_client.post(
            f"{base_url}/auth/login",
            json={
                "username": "testuser",
                "password": "testpass"
            }
        )
        assert response.status_code == 200
        assert 'token' in response.json()
        
        token = response.json()['token']
        
        # Access protected endpoint
        response = api_client.get(
            f"{base_url}/api/protected",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    def test_pagination(self, api_client, base_url):
        """Test API pagination"""
        
        response = api_client.get(
            f"{base_url}/api/users",
            params={"page": 1, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert len(data['items']) <= 10
