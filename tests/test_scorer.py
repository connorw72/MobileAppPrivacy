"""Tests for scorer.py."""
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scorer import calculate_score, _get_grade, _get_weight


class TestGetWeight:
    def test_known_type_financial(self):
        assert _get_weight("Financial Info") == 15.0

    def test_known_type_location(self):
        assert _get_weight("Location") == 12.0

    def test_known_type_diagnostics(self):
        assert _get_weight("Diagnostics") == 4.0

    def test_unknown_type_returns_default(self):
        assert _get_weight("Something Completely Unknown") == 5.0

    def test_partial_match(self):
        # "browsing history" contains "browsing history"
        assert _get_weight("browsing history") == 10.0


class TestGetGrade:
    def test_grade_a(self):
        assert _get_grade(95) == "A"
        assert _get_grade(90) == "A"

    def test_grade_b(self):
        assert _get_grade(85) == "B"
        assert _get_grade(80) == "B"

    def test_grade_c(self):
        assert _get_grade(75) == "C"
        assert _get_grade(70) == "C"

    def test_grade_d(self):
        assert _get_grade(65) == "D"
        assert _get_grade(60) == "D"

    def test_grade_f(self):
        assert _get_grade(59) == "F"
        assert _get_grade(0) == "F"


class TestCalculateScore:
    def test_no_data_collection_is_perfect(self):
        result = calculate_score({"tracked": [], "linked": [], "not_linked": [], "data_types": []})
        assert result["score"] == 100
        assert result["grade"] == "A"

    def test_tracked_data_penalised_more_than_linked(self):
        tracked_result = calculate_score({
            "tracked": ["Location"],
            "linked": [],
            "not_linked": [],
            "data_types": ["Location"],
        })
        linked_result = calculate_score({
            "tracked": [],
            "linked": ["Location"],
            "not_linked": [],
            "data_types": ["Location"],
        })
        assert tracked_result["score"] < linked_result["score"]

    def test_linked_penalised_more_than_not_linked(self):
        linked_result = calculate_score({
            "tracked": [],
            "linked": ["Location"],
            "not_linked": [],
            "data_types": ["Location"],
        })
        not_linked_result = calculate_score({
            "tracked": [],
            "linked": [],
            "not_linked": ["Location"],
            "data_types": ["Location"],
        })
        assert linked_result["score"] < not_linked_result["score"]

    def test_score_clamped_to_zero(self):
        # Many high-weight categories that would total far more than 100
        many_types = [
            "Financial Info", "Health & Fitness", "Location", "Contact Info",
            "Identifiers", "Browsing History", "Contacts", "Search History",
            "User Content", "Purchases", "Usage Data",
        ]
        result = calculate_score({
            "tracked": many_types,
            "linked": [],
            "not_linked": [],
            "data_types": many_types,
        })
        assert result["score"] == 0

    def test_score_never_exceeds_100(self):
        result = calculate_score({"tracked": [], "linked": [], "not_linked": [], "data_types": []})
        assert result["score"] <= 100

    def test_flat_data_types_only_treated_as_linked(self):
        result = calculate_score({
            "tracked": [],
            "linked": [],
            "not_linked": [],
            "data_types": ["Diagnostics"],
        })
        # Diagnostics weight=4, linked multiplier=1.2 → deduction=4.8 → score=95
        assert result["score"] == 95
        assert result["data_types_scored"]["diagnostics"]["category"] == "collected"

    def test_duplicate_data_type_not_double_counted(self):
        # Same type appears in both linked and not_linked; should only count once.
        result = calculate_score({
            "tracked": [],
            "linked": ["Location"],
            "not_linked": ["Location"],
            "data_types": ["Location"],
        })
        assert len(result["data_types_scored"]) == 1

    def test_result_contains_expected_keys(self):
        result = calculate_score({"tracked": [], "linked": ["Diagnostics"], "not_linked": [], "data_types": []})
        assert "score" in result
        assert "grade" in result
        assert "summary" in result
        assert "total_deduction" in result
        assert "data_types_scored" in result
