"""
Integration tests for Mergington High School Activities API
Tests all endpoints: GET /activities, POST /signup, DELETE /signup
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app
import src.app


@pytest.fixture
def client():
    """Create a test client for the API with fresh data"""
    # Reset activities to initial state before each test
    src.app.activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        # Verify expected activities exist
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activity_participants_are_strings(self, client):
        """Test that participants are email strings"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """Test successfully signing up a new participant"""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]

    def test_signup_duplicate_participant_fails(self, client):
        """Test that signing up twice fails"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for non-existent activity fails"""
        email = "student@mergington.edu"
        activity = "Non Existent Activity"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_updates_participant_list(self, client):
        """Test that signup actually adds participant to activity"""
        email = "verify@mergington.edu"
        activity = "Programming Class"
        
        # Get activities before signup
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity]["participants"].copy()
        
        # Signup
        response_signup = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response_signup.status_code == 200
        
        # Get activities after signup
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity]["participants"]
        
        # Verify participant was added
        assert len(participants_after) == len(participants_before) + 1
        assert email in participants_after


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_existing_participant_success(self, client):
        """Test successfully unregistering an existing participant"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Unregistered" in data["message"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering a non-participant fails"""
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from non-existent activity fails"""
        email = "student@mergington.edu"
        activity = "Non Existent Activity"
        
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_removes_participant_from_list(self, client):
        """Test that unregister actually removes participant from activity"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Get activities before unregister
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity]["participants"].copy()
        
        # Unregister
        response_delete = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response_delete.status_code == 200
        
        # Get activities after unregister
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity]["participants"]
        
        # Verify participant was removed
        assert len(participants_after) == len(participants_before) - 1
        assert email not in participants_after


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
