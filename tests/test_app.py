"""Tests for app.py Flask routes."""
import json
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


_SAMPLE_APP_DETAILS = {
    "trackId": 389801252,
    "trackName": "Instagram",
    "artistName": "Instagram, Inc.",
    "artworkUrl100": "https://example.com/icon.png",
    "primaryGenreName": "Photo & Video",
    "trackViewUrl": "https://apps.apple.com/us/app/instagram/id389801252",
    "description": "Share photos.",
}

_SAMPLE_SEARCH_RESULTS = [_SAMPLE_APP_DETAILS]

_SAMPLE_PRIVACY = {
    "tracked": [],
    "linked": ["Location", "Contact Info"],
    "not_linked": ["Diagnostics"],
    "data_types": ["Location", "Contact Info", "Diagnostics"],
}


class TestIndexRoute:
    def test_home_returns_200(self, client):
        rv = client.get("/")
        assert rv.status_code == 200
        assert b"AppPrivacy Score" in rv.data

    def test_home_contains_search_form(self, client):
        rv = client.get("/")
        assert b"search-input" in rv.data


class TestSearchRoute:
    @patch("app.search_app")
    def test_search_returns_json(self, mock_search, client):
        mock_search.return_value = _SAMPLE_SEARCH_RESULTS
        rv = client.get("/search?q=Instagram")
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert "results" in data
        assert data["results"][0]["name"] == "Instagram"

    def test_search_missing_query_returns_400(self, client):
        rv = client.get("/search")
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert "error" in data

    def test_search_empty_query_returns_400(self, client):
        rv = client.get("/search?q=")
        assert rv.status_code == 400

    @patch("app.search_app")
    def test_search_api_error_returns_500(self, mock_search, client):
        mock_search.side_effect = RuntimeError("iTunes unavailable")
        rv = client.get("/search?q=SomeApp")
        assert rv.status_code == 500
        data = json.loads(rv.data)
        assert "error" in data


class TestScoreRoute:
    @patch("app.calculate_score")
    @patch("app.scrape_privacy_details")
    @patch("app.get_app_details")
    def test_score_page_renders(self, mock_details, mock_scrape, mock_score, client):
        mock_details.return_value = _SAMPLE_APP_DETAILS
        mock_scrape.return_value = _SAMPLE_PRIVACY
        mock_score.return_value = {
            "score": 72,
            "grade": "C",
            "summary": "Fair privacy.",
            "total_deduction": 28.0,
            "data_types_scored": {},
        }
        rv = client.get("/score/389801252")
        assert rv.status_code == 200
        assert b"Instagram" in rv.data
        assert b"72" in rv.data

    @patch("app.get_app_details")
    def test_score_returns_404_when_app_not_found(self, mock_details, client):
        mock_details.return_value = None
        rv = client.get("/score/999999999")
        assert rv.status_code == 404
        assert b"App not found" in rv.data

    @patch("app.get_app_details")
    def test_score_returns_500_on_exception(self, mock_details, client):
        mock_details.side_effect = RuntimeError("Network error")
        rv = client.get("/score/389801252")
        assert rv.status_code == 500
        assert b"unexpected error" in rv.data.lower()
