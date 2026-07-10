"""
Locality extraction from NoBroker listing titles.

NoBroker titles follow a stable shape:

    <BHK> <Type> [In <ProjectName>] for <Rent|Lease|Sale> In <Locality> Bangalore

The real locality is the phrase AFTER the last "for <rent|lease|sale> in". The
original scraper split on the first " In ", which for the very common
"In <ProjectName> for Rent In <Locality>" shape returned the project name plus
marketing text as the "locality" (e.g. "Khan Mansion for Rent In Shanthi Nagar
Bangalore"), and even pulled a foreign city into it ("…Ranchi…" → geocoded
1,957 km away).

Design: case-insensitive, anchored on the rental clause, parenthetical
marketing/floor notes stripped. When no locality can be confidently extracted,
return None — downstream (commute.py) treats a null locality as "no origin" and
leaves the commute null, which the API already hides. Null beats junk.
"""

import re

# "for rent in" / "for lease in" / "for sale in", case-insensitive, flexible
# whitespace. Anchored on word boundaries so it never fires mid-word.
_RENTAL_CLAUSE = re.compile(r"\bfor\s+(?:rent|lease|sale)\s+in\s+", re.IGNORECASE)


def parse_locality(title):
    """Return the locality phrase from a listing title, or None if none is
    confidently extractable."""
    if not title or not title.strip():
        return None

    matches = list(_RENTAL_CLAUSE.finditer(title))
    if not matches:
        # No rental clause -> we cannot locate the locality reliably. Prefer a
        # null (handled downstream) over emitting a project name as a locality.
        return None

    # Everything after the LAST rental clause is the locality (handles the rare
    # case of a stray "for rent in" earlier in a project name).
    locality = title[matches[-1].end():]

    # Drop parenthetical marketing/floor notes: "( 3rd Floor, No Lift)", "( Nolift )".
    locality = re.sub(r"\([^)]*\)", " ", locality)
    # Collapse whitespace and trim stray edge punctuation.
    locality = re.sub(r"\s+", " ", locality).strip(" ,-")

    # Reject anything too short or without letters to be a real place name.
    if len(locality) < 3 or not re.search(r"[A-Za-z]", locality):
        return None

    return locality
