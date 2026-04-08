"""Tests for itunes.py using mocked HTTP responses."""
import json
import unittest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from itunes import get_app_details, search_app

_SAMPLE_APP = {
    "trackId": 389801252,
    "trackName": "Instagram",
    "artistName": "Instagram, Inc.",
    "artworkUrl100": "https://example.com/icon.png",
    "primaryGenreName": "Photo & Video",
    "description": "Capture and share photos.",
}


def _make_response(payload: dict, status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = payload
    mock.raise_for_status = MagicMock()
    return mock


class TestSearchApp:
    @patch("itunes.requests.get")
    def test_returns_results_list(self, mock_get):
        mock_get.return_value = _make_response({"results": [_SAMPLE_APP]})
        results = search_app("Instagram")
        assert len(results) == 1
        assert results[0]["trackName"] == "Instagram"

    @patch("itunes.requests.get")
    def test_empty_results(self, mock_get):
        mock_get.return_value = _make_response({"results": []})
        results = search_app("nonexistentapp12345")
        assert results == []

    @patch("itunes.requests.get")
    def test_sends_correct_params(self, mock_get):
        mock_get.return_value = _make_response({"results": []})
        search_app("TestApp", limit=3, country="gb")
        call_args = mock_get.call_args
        # params may be passed as a keyword arg or as the second positional arg
        if call_args.kwargs.get("params") is not None:
            params = call_args.kwargs["params"]
        elif len(call_args.args) > 1:
            params = call_args.args[1]
        else:
            params = call_args.kwargs["params"]
        assert params["term"] == "TestApp"
        assert params["limit"] == 3
        assert params["country"] == "gb"
        assert params["entity"] == "software"

    @patch("itunes.requests.get")
    def test_http_error_propagates(self, mock_get):
        import requests as req
        mock_resp = _make_response({}, 500)
        mock_resp.raise_for_status.side_effect = req.HTTPError("500 Server Error")
        mock_get.return_value = mock_resp
        try:
            search_app("anything")
            assert False, "Should have raised"
        except req.HTTPError:
            pass


class TestGetAppDetails:
    @patch("itunes.requests.get")
    def test_returns_first_result(self, mock_get):
        mock_get.return_value = _make_response({"results": [_SAMPLE_APP]})
        result = get_app_details(389801252)
        assert result is not None
        assert result["trackId"] == 389801252

    @patch("itunes.requests.get")
    def test_returns_none_when_no_results(self, mock_get):
        mock_get.return_value = _make_response({"results": []})
        result = get_app_details(999999999)
        assert result is None
