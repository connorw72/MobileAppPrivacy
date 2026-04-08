"""Tests for scraper.py using mocked HTTP responses."""
import json
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import (
    _classify_heading,
    _find_categories_in_text,
    _parse_privacy_api_node,
    scrape_privacy_details,
)


def _make_response(html: str = "", status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


class TestClassifyHeading:
    def test_tracked(self):
        assert _classify_heading("data used to track you") == "tracked"

    def test_linked(self):
        assert _classify_heading("data linked to you") == "linked"

    def test_not_linked(self):
        assert _classify_heading("data not linked to you") == "not_linked"

    def test_unknown_defaults_to_linked(self):
        assert _classify_heading("some other heading") == "linked"


class TestFindCategoriesInText:
    def test_finds_known_categories(self):
        text = "This app collects Location and Contact Info data."
        found = _find_categories_in_text(text)
        assert "Location" in found
        assert "Contact Info" in found

    def test_returns_empty_when_no_match(self):
        assert _find_categories_in_text("no personal data here") == []

    def test_case_insensitive(self):
        found = _find_categories_in_text("FINANCIAL INFO collected")
        assert "Financial Info" in found


class TestParsePrivacyApiNode:
    def test_empty_list_returns_empty_buckets(self):
        result = _parse_privacy_api_node([])
        assert result == {"tracked": [], "linked": [], "not_linked": [], "data_types": []}

    def test_parses_tracked_data(self):
        node = [
            {
                "privacyType": "Data Used to Track You",
                "dataCategories": [{"dataCategory": "Location"}],
            }
        ]
        result = _parse_privacy_api_node(node)
        assert "Location" in result["tracked"]
        assert "Location" in result["data_types"]

    def test_parses_linked_data(self):
        node = [
            {
                "privacyType": "Data Linked to You",
                "dataCategories": [{"dataCategory": "Contact Info"}],
            }
        ]
        result = _parse_privacy_api_node(node)
        assert "Contact Info" in result["linked"]

    def test_deduplicates_data_types(self):
        node = [
            {"privacyType": "Data Linked to You", "dataCategories": [{"dataCategory": "Location"}]},
            {"privacyType": "Data Not Linked to You", "dataCategories": [{"dataCategory": "Location"}]},
        ]
        result = _parse_privacy_api_node(node)
        assert result["data_types"].count("Location") == 1


class TestScrapePrivacyDetails:
    @patch("scraper.requests.get")
    def test_returns_error_on_request_failure(self, mock_get):
        import requests as req
        mock_resp = _make_response()
        mock_resp.raise_for_status.side_effect = req.RequestException("timeout")
        mock_get.return_value = mock_resp
        result = scrape_privacy_details(389801252)
        assert "error" in result

    @patch("scraper.requests.get")
    def test_parses_next_data_json(self, mock_get):
        """Scraper should extract privacy info from __NEXT_DATA__ JSON."""
        privacy_node = [
            {
                "privacyType": "Data Linked to You",
                "dataCategories": [{"dataCategory": "Identifiers"}],
            }
        ]
        next_data = {
            "props": {
                "pageProps": {
                    "privacyDetails": privacy_node
                }
            }
        }
        html = (
            f'<html><body>'
            f'<script id="__NEXT_DATA__" type="application/json">'
            f'{json.dumps(next_data)}'
            f'</script></body></html>'
        )
        mock_get.return_value = _make_response(html)
        result = scrape_privacy_details(389801252)
        assert "Identifiers" in result["data_types"]
        assert "Identifiers" in result["linked"]

    @patch("scraper.requests.get")
    def test_falls_back_to_text_search(self, mock_get):
        """Scraper should find categories in plain HTML text when no JSON/section."""
        html = "<html><body><p>This app collects Location and Diagnostics.</p></body></html>"
        mock_get.return_value = _make_response(html)
        result = scrape_privacy_details(389801252)
        assert "Location" in result["data_types"]
        assert "Diagnostics" in result["data_types"]

    @patch("scraper.requests.get")
    def test_parses_html_privacy_section(self, mock_get):
        """Scraper should parse structured HTML privacy sections."""
        html = """
        <html><body>
          <section class="app-privacy">
            <h3>Data Linked to You</h3>
            <ul><li>Financial Info</li><li>Location</li></ul>
            <h3>Data Not Linked to You</h3>
            <ul><li>Diagnostics</li></ul>
          </section>
        </body></html>
        """
        mock_get.return_value = _make_response(html)
        result = scrape_privacy_details(389801252)
        assert "Financial Info" in result["data_types"]
        assert "Diagnostics" in result["data_types"]
