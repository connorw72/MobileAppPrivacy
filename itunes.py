"""iTunes Search API integration for looking up mobile apps."""
import requests

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"


def search_app(query: str, limit: int = 5, country: str = "us") -> list:
    """Search for apps using the iTunes Search API.

    Args:
        query: The app name or keyword to search for.
        limit: Maximum number of results to return (default 5).
        country: Two-letter ISO country code (default "us").

    Returns:
        A list of app result dicts from the iTunes API.
    """
    params = {
        "term": query,
        "entity": "software",
        "limit": limit,
        "country": country,
    }
    response = requests.get(ITUNES_SEARCH_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])


def get_app_details(app_id: int, country: str = "us") -> dict | None:
    """Get detailed information for a specific app by its iTunes ID.

    Args:
        app_id: The iTunes track/app ID.
        country: Two-letter ISO country code (default "us").

    Returns:
        A dict of app details, or None if not found.
    """
    params = {
        "id": app_id,
        "entity": "software",
        "country": country,
    }
    response = requests.get(ITUNES_LOOKUP_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    results = data.get("results", [])
    return results[0] if results else None
