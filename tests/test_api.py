"""
Tests for the High School Management System API endpoints
"""

import pytest
from fastapi import status


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test successful retrieval of all activities"""
        response = client.get("/activities")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # Should have 9 activities
        
        # Verify some known activities exist
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check structure of Chess Club
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_activities_initial_participants(self, client):
        """Test that activities have initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have Michael and Daniel
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful student signup"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Signed up newstudent@mergington.edu for Chess Club"
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup to non-existent activity"""
        response = client.post(
            "/activities/NonExistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_registered(self, client):
        """Test signup when student is already registered"""
        # Michael is already signed up for Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Student already signed up"

    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple different activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == status.HTTP_200_OK
        
        # Sign up for Programming Class
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response2.status_code == status.HTTP_200_OK
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]

    def test_signup_with_special_characters_in_activity_name(self, client):
        """Test signup with URL-encoded activity names"""
        # "Soccer Team" should work
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": "newsoccer@mergington.edu"}
        )
        assert response.status_code == status.HTTP_200_OK


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful student unregistration"""
        # Michael is initially signed up for Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Unregistered michael@mergington.edu from Chess Club"
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/NonExistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_student_not_signed_up(self, client):
        """Test unregister when student is not signed up"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notsignedup@mergington.edu"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Student not signed up for this activity"

    def test_unregister_then_signup_again(self, client):
        """Test that a student can unregister and then sign up again"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Unregister
        response1 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response1.status_code == status.HTTP_200_OK
        
        # Sign up again
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == status.HTTP_200_OK
        
        # Verify student is signed up again
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]


class TestWorkflow:
    """Integration tests for common workflows"""

    def test_complete_signup_and_unregister_workflow(self, client):
        """Test a complete workflow of signing up and unregistering"""
        email = "workflow@mergington.edu"
        activity = "Drama Club"
        
        # Step 1: Get initial activities
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Step 2: Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Step 3: Verify signup
        after_signup_response = client.get("/activities")
        after_signup_data = after_signup_response.json()
        assert email in after_signup_data[activity]["participants"]
        assert len(after_signup_data[activity]["participants"]) == initial_count + 1
        
        # Step 4: Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # Step 5: Verify unregistration
        after_unregister_response = client.get("/activities")
        after_unregister_data = after_unregister_response.json()
        assert email not in after_unregister_data[activity]["participants"]
        assert len(after_unregister_data[activity]["participants"]) == initial_count

    def test_all_activities_accessible(self, client):
        """Test that all activities can be signed up for"""
        email = "allactivities@mergington.edu"
        
        # Get all activities
        response = client.get("/activities")
        all_activities = response.json()
        
        # Try to sign up for each activity
        for activity_name in all_activities.keys():
            signup_response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert signup_response.status_code == status.HTTP_200_OK, \
                f"Failed to sign up for {activity_name}"
