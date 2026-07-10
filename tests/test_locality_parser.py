"""
Fixture-based unit tests for locality.parse_locality.

Titles are REAL NoBroker titles pulled from the local DB (including the two
known-bad rows: "Khan Mansion" and the "…Ranchi…" row). Pure function tests —
no DB, no network — so they are fast and rerunnable.

The Ranchi row is expected to parse to its stated locality ("Old Argora Chowk
Bangalore"); it is still geographically wrong (that locality is in Ranchi), but
that is the outlier guard's job at commute time, not the parser's.

Usage:  venv/Scripts/python.exe tests/test_locality_parser.py
Exit 0 = all cases pass, 1 = any fail.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from locality import parse_locality  # noqa: E402

# (title, expected_locality)
CASES = [
    # simple "for rent in <locality>" — already correct, must stay stable
    ("3 BHK Flat for Rent  In Kodigehalli Bangalore", "Kodigehalli Bangalore"),
    ("3 BHK House for Rent  In Thindlu Bangalore", "Thindlu Bangalore"),
    ("4 BHK House for Rent  In Annasandrapalya Extension Bangalore", "Annasandrapalya Extension Bangalore"),
    # "In <Project> for Rent In <locality>" — old parser returned junk
    ("3 BHK Flat In Nimra  for Rent  In Nagawara Bangalore", "Nagawara Bangalore"),
    ("3 BHK Flat In Sneha Aprts for Rent  In Vijayanagar Bangalore", "Vijayanagar Bangalore"),
    ("3 BHK Flat In Whitefield for Rent  In Whitefield Bangalore", "Whitefield Bangalore"),
    ("3 BHK Flat In Stand Alone Building  for Rent  In Kaggadasapura Bangalore", "Kaggadasapura Bangalore"),
    ("3 BHK Apartment In Bda Indraprashta for Rent  In  Kengeri Satellite Town Bangalore", "Kengeri Satellite Town Bangalore"),
    ("3 BHK Flat In S K Layout  for Rent  In Electronic City Phase 1 S K Layout Bangalore", "Electronic City Phase 1 S K Layout Bangalore"),
    # known-bad rows from the audit
    ("3 BHK In Khan Mansion for Rent  In Shanthi Nagar Bangalore", "Shanthi Nagar Bangalore"),
    ("3 BHK Flat In Jaishree Green City Ranchi for Rent  In Old Argora Chowk Bangalore", "Old Argora Chowk Bangalore"),
    # "for Lease" variant
    ("3 BHK Flat In South Avenue for Lease  In Gottigere Bangalore", "Gottigere Bangalore"),
    # parenthetical floor/marketing notes stripped
    ("3 BHK Flat for Rent  In Shanti Nagar ( 3rd Floor, No Lift) Bangalore", "Shanti Nagar Bangalore"),
    ("3 BHK Apartment In Passcode  Sudam Nagar for Rent  In Lal Bagh Road ( Nolift, 3rd Floor) Bangalore", "Lal Bagh Road Bangalore"),
    # double spaces collapsed
    ("3 BHK Flat In Elin Mahaveer  for Rent  In  Electronic City  Bangalore", "Electronic City Bangalore"),
    # full-address locality passes through (geocodable)
    ("3 BHK Flat In Ashirvad for Rent  In 490, 14th B Cross Rd, Mahalakshmipuram Layout, Nagapura, Bengaluru, Karnataka 560086, India Bangalore",
     "490, 14th B Cross Rd, Mahalakshmipuram Layout, Nagapura, Bengaluru, Karnataka 560086, India Bangalore"),
    # no confidently-extractable locality -> None (null beats junk)
    ("", None),
    ("   ", None),
    (None, None),
    ("3 BHK Flat available near MG Road", None),  # no rental clause
]


def main():
    passed = 0
    failed = []
    for title, expected in CASES:
        got = parse_locality(title)
        if got == expected:
            passed += 1
        else:
            failed.append((title, expected, got))

    print("\n" + "=" * 60)
    print(" LOCALITY PARSER UNIT TESTS")
    print("=" * 60)
    print(f"  {passed}/{len(CASES)} cases passed")
    for title, expected, got in failed:
        print(f"  FAIL: {title!r}\n        expected {expected!r}, got {got!r}")
    print("=" * 60)
    ok = not failed
    print(f" RESULT: {'ALL PASS' if ok else str(len(failed)) + ' FAILED'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
