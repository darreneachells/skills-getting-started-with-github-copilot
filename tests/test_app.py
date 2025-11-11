"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that returned activities include expected activity names"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Drama Club",
            "Art Society",
            "Math Club",
            "Debate Team"
        ]
        
        for activity in expected_activities:
            assert activity in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Activity {activity_name} missing field {field}"

    def test_participants_is_list(self):
        """Test that participants field is a list"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_returns_200_for_valid_activity_and_new_participant(self):
        """Test successful signup returns 200 status code"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds the participant to the activity"""
        # First, get initial participant count
        response_before = client.get("/activities")
        activities_before = response_before.json()
        initial_count = len(activities_before["Chess Club"]["participants"])
        
        # Signup a new participant
        email = "unique_test_student@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Check that participant was added
        response_after = client.get("/activities")
        activities_after = response_after.json()
        final_count = len(activities_after["Chess Club"]["participants"])
        
        assert final_count == initial_count + 1
        assert email in activities_after["Chess Club"]["participants"]

    def test_signup_returns_error_for_nonexistent_activity(self):
        """Test that signup returns 404 for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_returns_error_for_duplicate_signup(self):
        """Test that signup returns 400 if student already signed up"""
        # First signup
        email = "duplicate_test@mergington.edu"
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        # Try to signup again
        response = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_returns_success_message(self):
        """Test that successful signup returns appropriate message"""
        email = "success_test@mergington.edu"
        response = client.post(
            f"/activities/Gym Class/signup?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_removes_participant(self):
        """Test that unregister removes the participant from activity"""
        # First, signup a participant
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Verify they were added
        response = client.get("/activities")
        assert email in response.json()["Drama Club"]["participants"]
        
        # Now unregister them
        response = client.post(
            f"/activities/Drama Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify they were removed
        response = client.get("/activities")
        assert email not in response.json()["Drama Club"]["participants"]

    def test_unregister_returns_200_for_valid_unregister(self):
        """Test that unregister returns 200 status code for valid operation"""
        # Signup first
        email = "valid_unregister@mergington.edu"
        client.post(f"/activities/Soccer Team/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Soccer Team/unregister?email={email}"
        )
        assert response.status_code == 200

    def test_unregister_returns_error_for_nonexistent_activity(self):
        """Test that unregister returns 404 for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_returns_error_if_not_signed_up(self):
        """Test that unregister returns 400 if participant not signed up"""
        response = client.post(
            "/activities/Basketball Club/unregister?email=not_signed_up@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_returns_success_message(self):
        """Test that successful unregister returns appropriate message"""
        # Signup first
        email = "success_unregister@mergington.edu"
        client.post(f"/activities/Art Society/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Art Society/unregister?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
