"""Language code parsing utilities for BCP-47 style codes."""

from __future__ import annotations

import re
from typing import Optional, Tuple


def normalize_script(script: str) -> str:
    """
    Normalize script name to a standard form.

    Handles both ISO 15924 4-letter codes and common names.

    Args:
        script: Script name or code (e.g., "Latn", "latin", "cyrillic", "Cyrl")

    Returns:
        Normalized lowercase script name.

    Examples:
        >>> normalize_script("Latn")
        'latin'
        >>> normalize_script("cyrillic")
        'cyrillic'
        >>> normalize_script("Syll")
        'syllabics'
    """
    script_lower = script.lower()

    # ISO 15924 4-letter codes
    if script_lower in ("latn", "latin"):
        return "latin"
    if script_lower in ("cyrl", "cyrillic"):
        return "cyrillic"
    if script_lower in ("syll", "syllabics"):
        return "syllabics"
    if script_lower in ("hebr", "hebrew"):
        return "hebrew"
    if script_lower in ("arab", "arabic"):
        return "arabic"
    if script_lower in ("hans", "simplified"):
        return "hans"
    if script_lower in ("hant", "traditional"):
        return "hant"

    return script_lower


def parse_language_code(
    code: str,
    explicit_script: Optional[str] = None,
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Parse a language code with optional script and region components.

    Supports BCP-47 style codes like:
    - "es" → ("es", None, None)
    - "es-ES" → ("es", None, "ES") - region preserved
    - "yi-Latn" → ("yi", "latin", None) - script extracted
    - "tt-cyrillic" → ("tt", "cyrillic", None) - script extracted
    - "zh-Hans-CN" → ("zh", "hans", "CN") - script extracted, region preserved

    If an explicit script is provided, it always takes precedence over
    any script extracted from the code.

    Args:
        code: Language code, possibly with script/region subtags.
        explicit_script: Optional explicit script that overrides extracted script.

    Returns:
        Tuple of (language_code, script_or_none, region_or_none).

    Examples:
        >>> parse_language_code("es")
        ('es', None, None)
        >>> parse_language_code("es-ES")
        ('es', None, 'ES')
        >>> parse_language_code("yi-Latn")
        ('yi', 'latin', None)
        >>> parse_language_code("tt-cyrillic")
        ('tt', 'cyrillic', None)
        >>> parse_language_code("zh-Hans-CN")
        ('zh', 'hans', 'CN')
        >>> parse_language_code("yi-Latn", "hebrew")
        ('yi', 'hebrew', None)
    """
    # Parse the code
    parts = code.split("-")
    language = parts[0].lower()
    extracted_script: Optional[str] = None
    extracted_region: Optional[str] = None

    # Look for script and region in remaining parts
    for part in parts[1:]:
        # ISO 15924 script codes are 4 letters with Title case (e.g., Latn, Cyrl)
        if len(part) == 4 and part[0].isupper() and extracted_script is None:
            extracted_script = normalize_script(part)
        # Also check for lowercase script names (e.g., "cyrillic", "latin")
        elif part.lower() in (
            "latin",
            "cyrillic",
            "syllabics",
            "hebrew",
            "arabic",
            "hans",
            "hant",
            "latn",
            "cyrl",
            "syll",
            "hebr",
            "arab",
        ) and extracted_script is None:
            extracted_script = normalize_script(part)
        # Region codes (2 uppercase letters or 3 digits)
        elif len(part) == 2 and part.isupper() and extracted_region is None:
            extracted_region = part.upper()
        elif len(part) == 3 and part.isdigit() and extracted_region is None:
            extracted_region = part  # UN M49 numeric region code

    # Use explicit script if provided
    if explicit_script is not None:
        extracted_script = normalize_script(explicit_script)

    return language, extracted_script, extracted_region
