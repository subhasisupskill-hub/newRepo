import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


BASELINE_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: restore the shared in-memory data before each test.
    activities.clear()
    activities.update(copy.deepcopy(BASELINE_ACTIVITIES))
    yield
    activities.clear()
    activities.update(copy.deepcopy(BASELINE_ACTIVITIES))


@pytest.fixture
def client():
    # Arrange: create a test client for the FastAPI app.
    with TestClient(app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_catalog(client):
    # Arrange
    path = "/activities"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["description"].startswith("Learn strategies")


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email_address = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_address},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email_address} for {activity_name}"
    assert email_address in activities[activity_name]["participants"]


def test_duplicate_signup_returns_bad_request(client):
    # Arrange
    activity_name = "Chess Club"
    email_address = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_address},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_removes_student(client):
    # Arrange
    activity_name = "Chess Club"
    email_address = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email_address},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email_address} from {activity_name}"
    assert email_address not in activities[activity_name]["participants"]


def test_missing_activity_returns_not_found(client):
    # Arrange
    activity_name = "Unknown Activity"
    email_address = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_address},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
