from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


def activity_signup_url(activity_name):
    return f"/activities/{quote(activity_name, safe='')}/signup"


@pytest.fixture
def sample_activities(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["existing@mergington.edu"],
        },
        "Art Club": {
            "description": "Make art",
            "schedule": "Wednesdays",
            "max_participants": 15,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(sample_activities):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_current_activities(client, sample_activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == sample_activities


def test_signup_adds_participant(client, sample_activities):
    activity_name = "Chess Club"
    email = "new@mergington.edu"

    response = client.post(
        activity_signup_url(activity_name),
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in sample_activities[activity_name]["participants"]
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client, sample_activities):
    activity_name = "Chess Club"
    email = "existing@mergington.edu"

    response = client.delete(
        activity_signup_url(activity_name),
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert sample_activities[activity_name]["participants"] == []


def test_unregister_returns_404_for_unknown_participant(client):
    response = client.delete(
        activity_signup_url("Chess Club"),
        params={"email": "unknown@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
