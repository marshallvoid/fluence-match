import re
from difflib import SequenceMatcher


def is_empty_like_pattern(s: str) -> bool:
    # Matches common empty patterns like "", '', ```, whitespace, and yaml/json/xml
    empty_pattern = r'^(?:json|xml|yaml)?[\s"`\'\n]*(?:\"\"|\'\')?[\s"`\'\n]*$'

    # If the string matches the empty pattern or contains no alphabetic characters
    return bool(re.fullmatch(empty_pattern, s)) or not re.search(r"[a-zA-Z]", s)


def similarity_ratio(s1: str, s2: str) -> float:
    return SequenceMatcher(None, s1, s2).ratio()
