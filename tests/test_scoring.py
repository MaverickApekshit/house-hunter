"""
Unit tests for scoring.py (pure, no I/O). Boundary cases, clamping, null-sqft
neutrality, weight normalization, and the non-null assertion.

pytest-discoverable (`test_*` functions) and runnable standalone:
    venv/Scripts/python.exe tests/test_scoring.py
Exit 0 = all pass, 1 = any fail.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import config    # noqa: E402
import scoring   # noqa: E402


# --- component sub-scores: boundaries + clamping ---
def test_rent_score_boundaries():
    assert scoring.rent_score(25000) == 100.0
    assert scoring.rent_score(45000) == 0.0
    assert scoring.rent_score(35000) == 50.0
    assert scoring.rent_score(20000) == 100.0   # clamp beyond ideal
    assert scoring.rent_score(50000) == 0.0     # clamp beyond limit


def test_commute_score_boundaries():
    assert scoring.commute_score(0) == 100.0
    assert scoring.commute_score(60) == 0.0
    assert scoring.commute_score(30) == 50.0
    assert scoring.commute_score(90) == 0.0     # clamp beyond max


def test_size_score_boundaries_and_null():
    assert scoring.size_score(1100) == 0.0
    assert scoring.size_score(1900) == 100.0
    assert scoring.size_score(1500) == 50.0
    assert scoring.size_score(900) == 0.0       # clamp
    assert scoring.size_score(2100) == 100.0    # clamp
    assert scoring.size_score(None) == 50.0     # neutral when unknown


# --- fit score: exact spec numbers ---
def test_fit_score_extremes():
    assert scoring.fit_score(25000, 0, 1900) == 100
    assert scoring.fit_score(45000, 60, 1100) == 0
    assert scoring.fit_score(35000, 30, 1500) == 50


def test_fit_score_null_sqft_is_neutral():
    # null sqft scores 50; with rent/commute mid it lands at 50 either way
    assert scoring.fit_score(35000, 30, None) == 50


def test_fit_score_sanity_vectors():
    # matches the brief's sanity vectors a > c > b
    a = scoring.fit_score(30000, 20, 1600)
    b = scoring.fit_score(44000, 55, 1200)
    c = scoring.fit_score(35000, 35, None)
    assert (a, b, c) == (70, 8, 47)
    assert a > c > b


def test_fit_score_requires_non_null_price_and_commute():
    for bad in ((None, 20, 1600), (30000, None, 1600)):
        try:
            scoring.fit_score(*bad)
            assert False, f"expected ValueError for {bad}"
        except ValueError:
            pass


def test_weight_normalization_when_overrides_dont_sum_to_100():
    saved = (config.SCORE_W_RENT, config.SCORE_W_COMMUTE, config.SCORE_W_SIZE)
    try:
        # Same ratio as default but summing to 200 -> must give the same result.
        config.SCORE_W_RENT, config.SCORE_W_COMMUTE, config.SCORE_W_SIZE = 90, 70, 40
        assert scoring.fit_score(30000, 20, 1600) == 70
        # Equal weights -> simple mean of the three sub-scores.
        config.SCORE_W_RENT, config.SCORE_W_COMMUTE, config.SCORE_W_SIZE = 1, 1, 1
        expected = round((scoring.rent_score(30000) + scoring.commute_score(20) + scoring.size_score(1600)) / 3)
        assert scoring.fit_score(30000, 20, 1600) == expected
    finally:
        config.SCORE_W_RENT, config.SCORE_W_COMMUTE, config.SCORE_W_SIZE = saved


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            failed.append((t.__name__, str(e) or "assertion failed"))
        except Exception as e:  # noqa: BLE001
            failed.append((t.__name__, f"{type(e).__name__}: {e}"))

    print("\n" + "=" * 52)
    print(" SCORING UNIT TESTS")
    print("=" * 52)
    print(f"  {passed}/{len(tests)} passed")
    for name, err in failed:
        print(f"  FAIL {name}: {err}")
    print("=" * 52)
    ok = not failed
    print(f" RESULT: {'ALL PASS' if ok else str(len(failed)) + ' FAILED'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
