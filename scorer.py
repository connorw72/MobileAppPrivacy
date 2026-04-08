"""Privacy scoring logic for mobile apps based on collected data types."""

# Deduction points (out of 100) for each Apple privacy label category.
# Higher value = more privacy-invasive.
_DATA_TYPE_WEIGHTS: dict[str, float] = {
    "financial info": 15.0,
    "health & fitness": 15.0,
    "sensitive info": 14.0,
    "location": 12.0,
    "contact info": 10.0,
    "identifiers": 10.0,
    "browsing history": 10.0,
    "contacts": 9.0,
    "search history": 8.0,
    "user content": 8.0,
    "purchases": 8.0,
    "usage data": 6.0,
    "diagnostics": 4.0,
    "other data": 3.0,
}

# Default deduction for a category not in the table above.
_DEFAULT_WEIGHT: float = 5.0

# Multipliers applied per privacy bucket.
_TRACKED_MULTIPLIER: float = 1.5   # data used for cross-site tracking
_LINKED_MULTIPLIER: float = 1.2    # data linked to the user's identity
_NOT_LINKED_MULTIPLIER: float = 1.0  # data not linked to the user's identity


def calculate_score(privacy_data: dict) -> dict:
    """Calculate a privacy score (0–100) for an app.

    100 = fully private (no data collection).
    0   = extremely invasive (maximum data collection).

    Args:
        privacy_data: Dict returned by :func:`scraper.scrape_privacy_details`,
            containing ``tracked``, ``linked``, ``not_linked``, and
            ``data_types`` lists.

    Returns:
        Dict with keys:
          - ``score``            – integer 0–100
          - ``grade``            – letter grade A–F
          - ``total_deduction``  – total points deducted from 100
          - ``data_types_scored``– per-type breakdown dict
          - ``summary``          – human-readable description
    """
    tracked = [t.lower() for t in privacy_data.get("tracked", [])]
    linked = [l.lower() for l in privacy_data.get("linked", [])]
    not_linked = [n.lower() for n in privacy_data.get("not_linked", [])]
    flat = [t.lower() for t in privacy_data.get("data_types", [])]

    total_deduction: float = 0.0
    scored: dict = {}

    for data_type in tracked:
        weight = _get_weight(data_type)
        deduction = weight * _TRACKED_MULTIPLIER
        scored[data_type] = {"weight": weight, "category": "tracked", "deduction": round(deduction, 1)}
        total_deduction += deduction

    for data_type in linked:
        if data_type not in scored:
            weight = _get_weight(data_type)
            deduction = weight * _LINKED_MULTIPLIER
            scored[data_type] = {"weight": weight, "category": "linked", "deduction": round(deduction, 1)}
            total_deduction += deduction

    for data_type in not_linked:
        if data_type not in scored:
            weight = _get_weight(data_type)
            deduction = weight * _NOT_LINKED_MULTIPLIER
            scored[data_type] = {"weight": weight, "category": "not_linked", "deduction": round(deduction, 1)}
            total_deduction += deduction

    # If only a flat list was provided (no bucket breakdown), treat as linked.
    if not tracked and not linked and not not_linked:
        for data_type in flat:
            if data_type not in scored:
                weight = _get_weight(data_type)
                deduction = weight * _LINKED_MULTIPLIER
                scored[data_type] = {"weight": weight, "category": "collected", "deduction": round(deduction, 1)}
                total_deduction += deduction

    final_score = max(0, min(100, round(100 - total_deduction)))

    return {
        "score": final_score,
        "grade": _get_grade(final_score),
        "total_deduction": round(total_deduction, 1),
        "data_types_scored": scored,
        "summary": _get_summary(final_score),
    }


def _get_weight(data_type: str) -> float:
    """Return the privacy-impact weight for *data_type*."""
    dt = data_type.lower()
    for key, weight in _DATA_TYPE_WEIGHTS.items():
        if key in dt or dt in key:
            return weight
    return _DEFAULT_WEIGHT


def _get_grade(score: int) -> str:
    """Convert a numeric score to a letter grade."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _get_summary(score: int) -> str:
    """Return a short human-readable description for a privacy score."""
    if score >= 90:
        return "Excellent privacy practices. Minimal data collection."
    if score >= 80:
        return "Good privacy practices. Limited data collection."
    if score >= 70:
        return "Fair privacy practices. Moderate data collection."
    if score >= 60:
        return "Poor privacy practices. Significant data collection."
    if score >= 50:
        return "Very poor privacy practices. Extensive data collection."
    return "Critically poor privacy practices. Massive data collection."
