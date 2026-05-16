"""
Performance/Load Tests - resource-intensive tests
These run on dedicated on-premise HCI infrastructure for consistent performance
"""

import time
from locust import HttpUser, task, between, events
from locust.runners import STATE_STOPPING, STATE_STOPPED


class APIUser(HttpUser):
    """Simulated user for load testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    host = "https://api.example.com"
    
    def on_start(self):
        """Called when a user starts"""
        # Login or setup
        self.client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
    
    @task(3)  # Weight: 3x more likely than other tasks
    def get_users(self):
        """GET /api/users endpoint"""
        with self.client.get(
            "/api/users",
            catch_response=True,
            name="GET /api/users"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def get_user_detail(self):
        """GET /api/users/{id} endpoint"""
        user_id = 12345
        with self.client.get(
            f"/api/users/{user_id}",
            catch_response=True,
            name="GET /api/users/:id"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("User not found")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def create_user(self):
        """POST /api/users endpoint"""
        with self.client.post(
            "/api/users",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "age": 25
            },
            catch_response=True,
            name="POST /api/users"
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed to create user: {response.status_code}")
    
    @task(1)
    def update_user(self):
        """PUT /api/users/{id} endpoint"""
        user_id = 12345
        with self.client.put(
            f"/api/users/{user_id}",
            json={
                "name": "Updated Name",
                "age": 26
            },
            catch_response=True,
            name="PUT /api/users/:id"
        ) as response:
            if response.status_code in [200, 204]:
                response.success()
            else:
                response.failure(f"Failed to update user: {response.status_code}")
    
    @task(1)
    def search_users(self):
        """GET /api/users/search endpoint"""
        with self.client.get(
            "/api/users/search?q=test&page=1&limit=50",
            catch_response=True,
            name="GET /api/users/search"
        ) as response:
            if response.status_code == 200:
                # Check response time
                if response.elapsed.total_seconds() > 2.0:
                    response.failure("Response took too long")
                else:
                    response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("="*80)
    print("LOAD TEST STARTING")
    print(f"Target: {environment.host}")
    print("="*80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("="*80)
    print("LOAD TEST COMPLETE")
    print("="*80)
    
    # Print summary statistics
    stats = environment.stats
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print("="*80)


# Stress test configuration
class StressTestUser(HttpUser):
    """High-intensity stress test user"""
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    host = "https://api.example.com"
    
    @task
    def rapid_fire_requests(self):
        """Make rapid requests to stress the system"""
        endpoints = [
            "/api/users",
            "/api/products",
            "/api/orders",
            "/api/health"
        ]
        
        for endpoint in endpoints:
            self.client.get(endpoint, name="Stress Test")


# Spike test configuration  
class SpikeTestUser(HttpUser):
    """Simulate sudden traffic spike"""
    
    wait_time = between(0.5, 1)
    host = "https://api.example.com"
    
    @task
    def spike_load(self):
        """Generate spike in traffic"""
        # Simulate burst of requests
        for _ in range(10):
            self.client.get("/api/users")
            time.sleep(0.1)
