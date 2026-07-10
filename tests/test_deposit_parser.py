"""
Fixture-based unit tests for scraper.extract_labeled_int.

The fixture reproduces the real NoBroker card-overview markup: each metric is a
`heading-6` value div immediately followed by its `heading-7` label div, all
inside one shared `flex-col` container. The old extractor climbed to that shared
container and concatenated every metric's digits — producing values like the
₹25,002,500 "deposit" (rent + deposit + area run together). The fix reads digits
from the label's own value node only.

Usage:  venv/Scripts/python.exe tests/test_deposit_parser.py
Exit 0 = all pass, 1 = any fail.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from bs4 import BeautifulSoup          # noqa: E402
from scraper import extract_labeled_int  # noqa: E402

# Rent ₹25,000 · Deposit ₹2,00,000 · Builtup 1,200 sqft — the shared container
# holds all three, so the OLD "all digits in the flex-col" approach would yield
# 25000·200000·1200 concatenated (a ₹25,002,500-style garbage value).
CARD = """
<div class="flex flex-col items-center card-overview">
  <div class="font-semi-bold heading-6" id="minimumRent"><span>&#8377;</span>25,000</div>
  <div class="flex heading-7">Rent</div>
  <div class="font-semi-bold heading-6" id="roomType"><span>&#8377;</span>2,00,000</div>
  <div class="flex heading-7">Deposit</div>
  <div class="font-semi-bold heading-6" id="minRent"><div class="flex" id="unitCode">1,200 sqft</div></div>
  <div class="heading-7">Builtup</div>
</div>
"""

# A card with no deposit metric at all -> must return None, never a guess.
CARD_NO_DEPOSIT = """
<div class="flex flex-col items-center card-overview">
  <div class="font-semi-bold heading-6" id="minRent"><div class="flex" id="unitCode">980 sqft</div></div>
  <div class="heading-7">Builtup</div>
</div>
"""


def main():
    soup = BeautifulSoup(CARD, "html.parser")
    rent = 25000
    deposit = extract_labeled_int(soup, "Deposit")
    area = extract_labeled_int(soup, "Builtup")

    concatenated_garbage = int("25000" + "200000" + "1200")  # what the old bug produced

    results = {
        "deposit_isolated_to_value_node": deposit == 200000,
        "deposit_not_concatenated": deposit != concatenated_garbage,
        "deposit_within_25x_rent": deposit is not None and deposit <= 25 * rent,
        "area_isolated_to_value_node": area == 1200,
        "missing_deposit_returns_none": extract_labeled_int(BeautifulSoup(CARD_NO_DEPOSIT, "html.parser"), "Deposit") is None,
    }

    print("\n" + "=" * 52)
    print(" DEPOSIT/AREA VALUE-NODE PARSER TESTS")
    print("=" * 52)
    print(f"  parsed: deposit={deposit}  area={area}  (old bug would give {concatenated_garbage})")
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("=" * 52)
    ok = all(results.values())
    print(f" RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
