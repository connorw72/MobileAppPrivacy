"""App Store scraper for extracting privacy label data from app pages."""
import json
import re

import requests
from bs4 import BeautifulSoup

APP_STORE_URL = "https://apps.apple.com/us/app/id{app_id}"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# All data categories defined in Apple's privacy nutrition labels.
KNOWN_CATEGORIES = [
    "Contact Info",
    "Health & Fitness",
    "Financial Info",
    "Location",
    "Sensitive Info",
    "Contacts",
    "User Content",
    "Browsing History",
    "Search History",
    "Identifiers",
    "Purchases",
    "Usage Data",
    "Diagnostics",
    "Other Data",
]

# Privacy section heading keywords → bucket mapping.
_BUCKET_KEYWORDS = {
    "track": "tracked",
    "link": "linked",
}


def scrape_privacy_details(app_id: int) -> dict:
    """Fetch and parse the App Store privacy labels for an app.

    Tries three strategies in order:
    1. Extract from Next.js ``__NEXT_DATA__`` JSON embedded in the page.
    2. Parse the HTML privacy section using known class names.
    3. Text-search the page for known Apple privacy category names.

    Args:
        app_id: The iTunes/App Store numeric app ID.

    Returns:
        A dict with keys:
          - ``tracked``   – list of data-type strings used to track the user
          - ``linked``    – list of data-type strings linked to the user
          - ``not_linked``– list of data-type strings not linked to the user
          - ``data_types``– deduplicated flat list of all collected data types
          - ``error``     – present only when the page could not be fetched
    """
    url = APP_STORE_URL.format(app_id=app_id)

    try:
        response = requests.get(url, headers=_HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {
            "error": str(exc),
            "tracked": [],
            "linked": [],
            "not_linked": [],
            "data_types": [],
        }

    soup = BeautifulSoup(response.text, "html.parser")

    # Strategy 1 – Next.js embedded JSON
    next_script = soup.find("script", id="__NEXT_DATA__")
    if next_script:
        try:
            next_data = json.loads(next_script.string or "{}")
            privacy = _find_privacy_in_next_data(next_data)
            if privacy:
                return privacy
        except (json.JSONDecodeError, AttributeError):
            pass

    # Strategy 2 – HTML privacy section
    privacy_section = _find_privacy_section(soup)
    if privacy_section:
        result = _parse_privacy_section(privacy_section)
        if result.get("data_types"):
            return result

    # Strategy 3 – keyword search in raw page text
    data_types = _find_categories_in_text(response.text)
    return {
        "tracked": [],
        "linked": data_types,
        "not_linked": [],
        "data_types": data_types,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_privacy_section(soup: BeautifulSoup):
    """Return the first element that looks like the App Store privacy section."""
    candidates = [
        soup.find("section", class_=re.compile(r"privacy", re.I)),
        soup.find("div", class_=re.compile(r"app-privacy", re.I)),
        soup.find(attrs={"data-testid": re.compile(r"privacy", re.I)}),
        soup.find(id=re.compile(r"privacy", re.I)),
    ]
    return next((c for c in candidates if c is not None), None)


def _parse_privacy_section(section) -> dict:
    """Parse a BeautifulSoup element containing the App Store privacy section."""
    result: dict = {"tracked": [], "linked": [], "not_linked": [], "data_types": []}

    for heading in section.find_all(["h2", "h3", "h4"]):
        heading_text = heading.get_text(strip=True).lower()
        next_list = heading.find_next(["ul", "ol"])
        if not next_list:
            continue
        items = [li.get_text(strip=True) for li in next_list.find_all("li") if li.get_text(strip=True)]
        bucket = _classify_heading(heading_text)
        result[bucket].extend(items)
        result["data_types"].extend(items)

    # Fallback – grab every list item in the section
    if not result["data_types"]:
        items = [li.get_text(strip=True) for li in section.find_all("li") if li.get_text(strip=True)]
        result["linked"] = items
        result["data_types"] = items

    result["data_types"] = list(dict.fromkeys(result["data_types"]))
    return result


def _classify_heading(heading_text: str) -> str:
    """Map a section heading string to a privacy bucket."""
    if "track" in heading_text:
        return "tracked"
    if "link" in heading_text and "not" not in heading_text:
        return "linked"
    if "not" in heading_text and "link" in heading_text:
        return "not_linked"
    return "linked"


def _find_privacy_in_next_data(data, _depth: int = 0) -> dict | None:
    """Recursively search a Next.js JSON tree for privacy label data."""
    if _depth > 12 or not isinstance(data, dict):
        return None

    for key in ("privacyDetails", "privacyTypes", "privacy"):
        if key in data:
            parsed = _parse_privacy_api_node(data[key])
            if parsed and parsed.get("data_types"):
                return parsed

    for value in data.values():
        if isinstance(value, dict):
            found = _find_privacy_in_next_data(value, _depth + 1)
            if found:
                return found
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    found = _find_privacy_in_next_data(item, _depth + 1)
                    if found:
                        return found
    return None


def _parse_privacy_api_node(node) -> dict:
    """Convert Apple's privacy API structure into our internal dict format."""
    result: dict = {"tracked": [], "linked": [], "not_linked": [], "data_types": []}

    if not isinstance(node, list):
        return result

    for item in node:
        if not isinstance(item, dict):
            continue
        purpose = (
            item.get("privacyType", item.get("purpose", item.get("label", "")))
            .lower()
        )
        categories = item.get("dataCategories", item.get("categories", []))
        cat_names = [
            (c.get("dataCategory", c.get("category", c.get("label", "")))
             if isinstance(c, dict) else str(c))
            for c in categories
        ]
        bucket = _classify_heading(purpose)
        result[bucket].extend(cat_names)
        result["data_types"].extend(cat_names)

    result["data_types"] = list(dict.fromkeys(result["data_types"]))
    return result


def _find_categories_in_text(text: str) -> list:
    """Return any known Apple privacy category names found in raw page text."""
    return [cat for cat in KNOWN_CATEGORIES if cat.lower() in text.lower()]
