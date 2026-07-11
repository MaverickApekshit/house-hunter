"""
Weighted fit score — the board's default ranking.

Pure functions, no I/O, computed at read time and never stored. Owner priorities
(config constants, env-overridable): lower rent 45% · shorter commute 35% ·
bigger flat 20%. Each component is a 0–100 sub-score; the fit score is their
weight-normalized average, rounded to an integer 0–100.
"""

import config


def _clamp(value, lo=0.0, hi=100.0):
    return max(lo, min(hi, value))


def rent_score(price):
    """100 at/below SCORE_RENT_MIN, 0 at/above SCORE_RENT_MAX, linear between."""
    span = config.SCORE_RENT_MAX - config.SCORE_RENT_MIN
    return _clamp((config.SCORE_RENT_MAX - price) / span * 100)


def commute_score(commute_mins):
    """100 at 0 min, 0 at/above SCORE_COMMUTE_MAX min, linear between."""
    return _clamp((1 - commute_mins / config.SCORE_COMMUTE_MAX) * 100)


def size_score(area_sqft):
    """0 at/below SCORE_SQFT_MIN, 100 at/above SCORE_SQFT_MAX; None -> 50 (neutral)."""
    if area_sqft is None:
        return 50.0
    span = config.SCORE_SQFT_MAX - config.SCORE_SQFT_MIN
    return _clamp((area_sqft - config.SCORE_SQFT_MIN) / span * 100)


def fit_score(price, commute_mins, area_sqft):
    """Weighted, normalized fit score as an integer 0–100.

    price and commute_mins are never null in served rows (the API filters
    guarantee it) — assert rather than silently defaulting. area_sqft may be
    null (treated as neutral by size_score).
    """
    if price is None or commute_mins is None:
        raise ValueError("fit_score requires non-null price and commute_mins")

    w_rent, w_commute, w_size = (
        config.SCORE_W_RENT, config.SCORE_W_COMMUTE, config.SCORE_W_SIZE,
    )
    total = w_rent + w_commute + w_size
    if total <= 0:
        raise ValueError("fit score weights must sum to a positive value")

    raw = (
        w_rent * rent_score(price)
        + w_commute * commute_score(commute_mins)
        + w_size * size_score(area_sqft)
    ) / total
    return round(raw)
