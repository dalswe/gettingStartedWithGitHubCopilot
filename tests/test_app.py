"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def setup_activities():
    """Reset activities to a known state before each test"""
    # Store original state
    original = {k: {"participants": v["participants"].copy()} for k, v in activities.items()}
    
    yield  # Run the test
    
    # Restore original state
    for activity_name, original_data in original.items():
        activities[activity_name]["participants"] = original_data["participants"]


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_has_required_fields(self, client):
        """Test that activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data.get("Chess Club")
        
        assert chess_club is not None
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client, setup_activities):
        """Test signing up a new participant"""
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        assert len(activities["Chess Club"]["participants"]) == initial_count + 1
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client, setup_activities):
        """Test that signing up the same person twice fails"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client, setup_activities):
        """Test that signing up for a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestUnregisterFromActivity:
    """Test the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client, setup_activities):
        """Test unregistering an existing participant"""
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client, setup_activities):
        """Test that unregistering a non-participant fails"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_from_nonexistent_activity_fails(self, client, setup_activities):
        """Test that unregistering from a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_then_unregister(self, client, setup_activities):
        """Test signing up and then unregistering a participant"""
        # Sign up
        signup_response = client.post(
            "/activities/Programming Class/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert signup_response.status_code == 200
        assert "testuser@mergington.edu" in activities["Programming Class"]["participants"]
        
        # Unregister
        unregister_response = client.post(
            "/activities/Programming Class/unregister",
            params={"email": "testuser@mergington.edu"}
        )
        assert unregister_response.status_code == 200
        assert "testuser@mergington.edu" not in activities["Programming Class"]["participants"]
    
    def test_multiple_participants_signup(self, client, setup_activities):
        """Test multiple participants signing up for the same activity"""
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                "/activities/Science Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are registered
        for email in emails:
            assert email in activities["Science Club"]["participants"]
