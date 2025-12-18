from typing import Optional


# Canonical ordering for grades / conditions.
# Lower index == better condition.
GRADE_ORDER = [
    "Near Mint",
    "PSA 6",
    "PSA 7",
    "PSA 8",
    "PSA 9",
    "PSA 10",
]

_GRADE_INDEX = {name.lower(): idx for idx, name in enumerate(GRADE_ORDER)}


def normalize_grade(raw: Optional[str]) -> Optional[str]:
    """
    Normalize arbitrary grade labels into our canonical set where possible.

    Handles case-insensitivity and common aliases like 'nm', 'nm/mint', etc.
    Falls back to the trimmed input if we don't recognize the grade.
    """
    if not raw:
        return None

    value = raw.strip()
    if not value:
        return None

    lower = value.lower()

    # Common Near Mint aliases
    if lower in {"near mint", "nm", "nm/mint", "nm-mint", "nm-mt"}:
        return "Near Mint"

    # PSA grades (allow variants like 'psa10', 'psa-10', etc.)
    if "psa" in lower:
        # Extract the numeric part, if any
        digits = "".join(ch for ch in lower if ch.isdigit())
        if digits.isdigit():
            try:
                num = int(digits)
            except ValueError:
                num = None
            if num is not None and 1 <= num <= 10:
                return f"PSA {num}"

    # No known normalization – just return the trimmed value
    return value


def grade_rank(grade: Optional[str]) -> Optional[int]:
    """
    Return a numeric rank for the given grade.

    Lower numbers indicate better condition according to GRADE_ORDER.
    Unknown grades return None, so callers can decide how to sort them.
    """
    if not grade:
        return None

    normalized = normalize_grade(grade)
    if not normalized:
        return None

    return _GRADE_INDEX.get(normalized.lower())



