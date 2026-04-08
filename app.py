"""Flask web application for scoring mobile apps on privacy and security."""
import logging
import os

from flask import Flask, jsonify, render_template, request

from itunes import get_app_details, search_app
from scraper import scrape_privacy_details
from scorer import calculate_score

app = Flask(__name__)

_logger = logging.getLogger(__name__)


@app.route("/")
def index():
    """Render the home / search page."""
    return render_template("index.html")


@app.route("/search")
def search():
    """Search for apps via the iTunes API and return JSON results.

    Query params:
        q (str): Search term (required).

    Returns:
        JSON ``{"results": [...]}`` or ``{"error": "..."}`` with HTTP 400/500.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "No search query provided."}), 400

    try:
        raw_results = search_app(query, limit=5)
    except Exception as exc:
        _logger.exception("iTunes search failed for query %r", query)
        return jsonify({"error": "Search service unavailable. Please try again later."}), 500

    apps = [
        {
            "id": r.get("trackId"),
            "name": r.get("trackName"),
            "developer": r.get("artistName"),
            "icon": r.get("artworkUrl100"),
            "category": r.get("primaryGenreName"),
            "description": (r.get("description") or "")[:200],
        }
        for r in raw_results
    ]
    return jsonify({"results": apps})


@app.route("/score/<int:app_id>")
def score(app_id: int):
    """Scrape the App Store and display a privacy score for an app.

    Args:
        app_id: iTunes numeric app ID (from the URL path).
    """
    try:
        app_details = get_app_details(app_id)
        if not app_details:
            return render_template("result.html", error="App not found."), 404

        privacy_data = scrape_privacy_details(app_id)
        score_result = calculate_score(privacy_data)

        app_info = {
            "id": app_id,
            "name": app_details.get("trackName"),
            "developer": app_details.get("artistName"),
            "icon": app_details.get("artworkUrl100"),
            "category": app_details.get("primaryGenreName"),
            "store_url": app_details.get("trackViewUrl"),
        }

        return render_template(
            "result.html",
            app=app_info,
            privacy=privacy_data,
            score=score_result,
        )
    except Exception as exc:
        _logger.exception("Failed to score app %d", app_id)
        return render_template("result.html", error="An unexpected error occurred. Please try again."), 500


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
