#!/usr/bin/env python3
"""
Convert XPF Corpus rules and verify files to YAML or JSON format.

Usage:
    python convert_to_yaml.py <lang_code> <tsv_file> <data_root> <output_dir>
    python convert_to_yaml.py --all _ <tsv_file> <data_root> <output_dir>
    python convert_to_yaml.py --all --format json _ <tsv_file> <data_root> <output_dir>
    python convert_to_yaml.py --generate-index <tsv_file> <data_root>

Example:
    # Generate YAML for human review
    python convert_to_yaml.py --all _ langs-list.tsv ~/XPF/Data ./yaml_output

    # Generate JSON for package bundling
    python convert_to_yaml.py --all --format json _ langs-list.tsv ~/XPF/Data xpfcorpus/data/languages

    # Generate index.json
    python convert_to_yaml.py --generate-index langs-list.tsv ~/XPF/Data > xpfcorpus/data/index.json
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

# PyYAML is optional - only needed for YAML output
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_tsv(tsv_path: Path) -> dict[str, dict[str, Any]]:
    """Parse the langs-list.tsv file into a dictionary keyed by language code."""
    languages = {}
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            code = row.get("code", "").strip()
            if code:
                languages[code] = row
    return languages


def normalize_script_name(script: str) -> str:
    """Normalize script name to a standard form."""
    script_lower = script.lower()
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
    return script_lower


def detect_script_from_content(file_path: Path) -> str:
    """
    Detect the script used in a rules file by examining character ranges.

    Returns: detected script name or "unknown"
    """
    if not file_path.exists():
        return "unknown"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return "unknown"

    # Count characters in different script ranges
    cyrillic_count = 0
    hebrew_count = 0
    arabic_count = 0
    latin_count = 0
    greek_count = 0

    for char in content:
        cp = ord(char)
        # Cyrillic: U+0400–U+04FF, U+0500–U+052F
        if 0x0400 <= cp <= 0x052F:
            cyrillic_count += 1
        # Hebrew: U+0590–U+05FF
        elif 0x0590 <= cp <= 0x05FF:
            hebrew_count += 1
        # Arabic: U+0600–U+06FF, U+0750–U+077F
        elif 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F:
            arabic_count += 1
        # Greek: U+0370–U+03FF
        elif 0x0370 <= cp <= 0x03FF:
            greek_count += 1
        # Basic Latin letters (excluding ASCII punctuation/digits)
        elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
            latin_count += 1
        # Latin Extended-A, Extended-B, etc.
        elif 0x00C0 <= cp <= 0x024F:
            latin_count += 1

    # Determine dominant script (excluding latin since it's often in comments/syntax)
    # We look for non-Latin scripts first
    counts = [
        (cyrillic_count, "cyrillic"),
        (hebrew_count, "hebrew"),
        (arabic_count, "arabic"),
        (greek_count, "greek"),
    ]

    # If any non-Latin script has significant presence, use it
    max_count, max_script = max(counts, key=lambda x: x[0])
    if max_count > 10:  # Threshold to avoid false positives from IPA symbols
        return max_script

    # Default to latin if no other script detected
    return "latin"


def extract_script_name(rules_path: str, lang_code: str, data_root: Path) -> str:
    """
    Extract script name from rules filename, detecting from content if needed.

    Examples:
        es.rules -> latin (detected from content)
        mk.rules -> cyrillic (detected from content)
        tt-cyrillic.rules -> cyrillic (from filename)
        tt-latn.rules -> latin (from filename)
        iu-Latn.rules -> latin (from filename)
        iu-Syll.rules -> syllabics (from filename)
    """
    if not rules_path:
        return "unknown"

    filename = Path(rules_path).stem  # e.g., "tt-cyrillic" or "es"

    # If filename has a script suffix, extract it
    if filename.startswith(f"{lang_code}-"):
        script = filename[len(lang_code) + 1:]  # e.g., "cyrillic", "latn", "Latn", "Syll"
        return normalize_script_name(script)

    # No script suffix - detect from file content
    resolved_path = resolve_path(rules_path, data_root)
    return detect_script_from_content(resolved_path)


def parse_rules_file(rules_path: Path) -> dict[str, Any]:
    """
    Parse a .rules file into structured data.

    Rules files are CSV-like with format:
        type,sfrom,sto,weight,precede,follow,comment
    """
    rules: dict[str, Any] = {
        "classes": {},
        "pre": [],
        "match": [],
        "sub": [],
        "ipasub": [],
        "word": [],
    }

    if not rules_path.exists():
        return rules

    with open(rules_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Skip header line
            if line.startswith("type,"):
                continue

            # Parse CSV line (handle quoted fields with commas)
            try:
                reader = csv.reader([line])
                fields = next(reader)
            except Exception:
                continue

            if len(fields) < 3:
                continue

            rule_type = fields[0].strip()
            sfrom = fields[1] if len(fields) > 1 else ""
            sto = fields[2] if len(fields) > 2 else ""
            weight = fields[3] if len(fields) > 3 else ""
            precede = fields[4] if len(fields) > 4 else ""
            follow = fields[5] if len(fields) > 5 else ""
            comment = fields[6] if len(fields) > 6 else ""

            if rule_type == "class":
                rules["classes"][sfrom] = sto
            elif rule_type == "pre":
                rule: dict[str, Any] = {"from": sfrom, "to": sto}
                if comment:
                    rule["comment"] = comment
                rules["pre"].append(rule)
            elif rule_type == "match":
                rule = {"from": sfrom, "to": sto}
                if comment:
                    rule["comment"] = comment
                rules["match"].append(rule)
            elif rule_type == "sub":
                rule = {"from": sfrom, "to": sto}
                if weight:
                    try:
                        rule["weight"] = float(weight)
                    except ValueError:
                        pass
                if precede:
                    rule["precede"] = precede
                if follow:
                    rule["follow"] = follow
                if comment:
                    rule["comment"] = comment
                rules["sub"].append(rule)
            elif rule_type == "ipasub":
                rule = {"from": sfrom, "to": sto}
                if weight:
                    try:
                        rule["weight"] = float(weight)
                    except ValueError:
                        pass
                if precede:
                    rule["precede"] = precede
                if follow:
                    rule["follow"] = follow
                if comment:
                    rule["comment"] = comment
                rules["ipasub"].append(rule)
            elif rule_type == "word":
                rule = {"word": sfrom, "phonemes": sto}
                if comment:
                    rule["comment"] = comment
                rules["word"].append(rule)

    # Remove empty sections
    rules = {k: v for k, v in rules.items() if v}

    return rules


def parse_verify_file(verify_path: Path) -> list[dict[str, str]]:
    """
    Parse a .verify.csv file into a list of word/phoneme pairs.

    Format: word,phonemes,comment (comma or tab delimited)
    """
    verify: list[dict[str, str]] = []

    if not verify_path.exists():
        return verify

    with open(verify_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Filter out comments and empty lines
    data_lines = [line.strip() for line in lines
                  if line.strip() and not line.strip().startswith("#")]

    if not data_lines:
        return verify

    # Detect delimiter: if all lines have tabs, use tab; otherwise use csv.Sniffer
    if all("\t" in line for line in data_lines):
        dialect = csv.get_dialect("excel-tab")
    else:
        try:
            sample = "\n".join(data_lines[:10])
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.get_dialect("excel")

    reader = csv.reader(data_lines, dialect=dialect)
    for fields in reader:
        if len(fields) < 2:
            continue

        word = fields[0].strip()
        phonemes = fields[1].strip()
        comment = fields[2].strip() if len(fields) > 2 else ""

        if word and phonemes:
            entry: dict[str, str] = {"word": word, "phonemes": phonemes}
            if comment:
                entry["comment"] = comment
            verify.append(entry)

    return verify


def resolve_path(path_str: str, data_root: Path) -> Path:
    """Resolve a path from the TSV (relative to XPF root) to absolute path."""
    if not path_str:
        return Path()
    # Paths in TSV are like "Data/es_Spanish/es.rules"
    # data_root is the Data directory itself
    if path_str.startswith("Data/"):
        path_str = path_str[5:]  # Remove "Data/" prefix
    return data_root / path_str


def convert_language(
    lang_code: str,
    lang_data: dict[str, Any],
    data_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Convert a language's rules and verify files to structured data.

    Returns:
        Tuple of (full_data, index_entry) where:
        - full_data: Complete language data with metadata, scripts, rules, verify
        - index_entry: Summary for index.json with scripts and default
    """

    # Build metadata
    metadata: dict[str, Any] = {
        "code": lang_code,
        "name": lang_data.get("name", ""),
        "family": lang_data.get("family", ""),
        "macroarea": lang_data.get("macroarea", ""),
    }

    # Check if compromised
    rules_path = lang_data.get("rules", "")
    if "_compromised" in rules_path:
        compromised_info: dict[str, str] = {}
        # Affected sounds pattern (e.g., "p|b|t|d|k|ɡ|s|z")
        compromised_sounds = (lang_data.get("compromised") or "").strip()
        if compromised_sounds:
            compromised_info["sounds"] = compromised_sounds
        # Text description of the issue
        compromised_note = (lang_data.get("compromised_other") or "").strip()
        if compromised_note:
            compromised_info["note"] = compromised_note
        # Always include compromised key if language is compromised (even if empty)
        metadata["compromised"] = compromised_info if compromised_info else True

    # Collect all scripts
    scripts: dict[str, Any] = {}
    script_names: list[str] = []

    # First script
    rules_path_1 = lang_data.get("rules", "")
    verify_path_1 = lang_data.get("verify", "")

    if rules_path_1:
        script_name = extract_script_name(rules_path_1, lang_code, data_root)
        script_names.append(script_name)

        rules_file = resolve_path(rules_path_1, data_root)
        verify_file = resolve_path(verify_path_1, data_root)

        scripts[script_name] = {
            "verify": parse_verify_file(verify_file),
            "rules": parse_rules_file(rules_file),
        }

    # Track which script has no hyphen in filename (indicates default)
    script_without_hyphen: Optional[str] = None
    rules_filename_1 = Path(rules_path_1).stem if rules_path_1 else ""
    if rules_filename_1 == lang_code:  # No hyphen, just lang code
        script_without_hyphen = script_names[0] if script_names else None

    # Second script (if exists)
    rules_path_2 = lang_data.get("rules_2", "")
    verify_path_2 = lang_data.get("verify_2", "")

    if rules_path_2:
        script_name = extract_script_name(rules_path_2, lang_code, data_root)
        script_names.append(script_name)

        rules_file = resolve_path(rules_path_2, data_root)
        verify_file = resolve_path(verify_path_2, data_root)

        scripts[script_name] = {
            "verify": parse_verify_file(verify_file),
            "rules": parse_rules_file(rules_file),
        }

        # Check if second script has no hyphen
        rules_filename_2 = Path(rules_path_2).stem
        if rules_filename_2 == lang_code:
            script_without_hyphen = script_name

    # Determine default_script
    # If only one script, it's the default
    # If multiple scripts, the one without hyphen in filename is the default
    default_script: Optional[str] = None
    if len(scripts) == 1:
        default_script = script_names[0]
    elif script_without_hyphen:
        default_script = script_without_hyphen
    # else: no default_script - user must specify

    if default_script:
        metadata["default_script"] = default_script

    # Build full data structure
    full_data: dict[str, Any] = {
        "metadata": metadata,
        "scripts": scripts,
    }

    # Build index entry
    index_entry: dict[str, Any] = {
        "scripts": script_names,
        "default": default_script,
    }

    return full_data, index_entry


def represent_str(dumper: Any, data: str) -> Any:
    """Custom string representer to handle multiline and special characters."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    if any(c in data for c in ":#{}[]&*!|>'\"%@`"):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert XPF Corpus rules/verify files to YAML or JSON format."
    )
    parser.add_argument(
        "lang_code",
        nargs="?",
        help="Language code to convert (e.g., 'es', 'tt', 'aak'). Use '_' with --all.",
    )
    parser.add_argument(
        "tsv_file",
        type=Path,
        help="Path to langs-list.tsv file",
    )
    parser.add_argument(
        "data_root",
        type=Path,
        help="Root directory containing language data (the 'Data' folder)",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        nargs="?",
        help="Output directory for language files (not needed with --generate-index)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Convert all languages (lang_code is ignored)",
    )
    parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)",
    )
    parser.add_argument(
        "--generate-index",
        action="store_true",
        help="Generate index.json to stdout (ignores other options)",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.tsv_file.exists():
        print(f"Error: TSV file not found: {args.tsv_file}", file=sys.stderr)
        return 1

    if not args.data_root.exists():
        print(f"Error: Data root not found: {args.data_root}", file=sys.stderr)
        return 1

    # Parse language list
    languages = parse_tsv(args.tsv_file)

    # Handle --generate-index mode
    if args.generate_index:
        index: dict[str, Any] = {}
        for lang_code in languages:
            lang_data = languages[lang_code]
            try:
                _, index_entry = convert_language(lang_code, lang_data, args.data_root)
                index[lang_code] = index_entry
            except Exception as e:
                print(f"Warning: Error processing {lang_code}: {e}", file=sys.stderr)
        print(json.dumps(index, indent=2, ensure_ascii=False))
        return 0

    # Validate output_dir for non-index mode
    if not args.output_dir:
        parser.error("output_dir is required unless using --generate-index")

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Check YAML availability
    if args.format == "yaml" and not HAS_YAML:
        print("Error: PyYAML is required for YAML output. Install with: pip install pyyaml", file=sys.stderr)
        return 1

    # Set up custom YAML dumper if using YAML
    if args.format == "yaml" and HAS_YAML:
        yaml.add_representer(str, represent_str)

    if args.all:
        lang_codes = list(languages.keys())
    else:
        if not args.lang_code or args.lang_code == "_":
            parser.error("lang_code is required unless using --all")
        lang_codes = [args.lang_code]

    for lang_code in lang_codes:
        if lang_code not in languages:
            print(f"Warning: Language code '{lang_code}' not found in TSV", file=sys.stderr)
            continue

        lang_data = languages[lang_code]

        try:
            full_data, _ = convert_language(lang_code, lang_data, args.data_root)

            if args.format == "json":
                output_file = args.output_dir / f"{lang_code}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(full_data, f, indent=2, ensure_ascii=False)
            else:
                output_file = args.output_dir / f"{lang_code}.yaml"
                with open(output_file, "w", encoding="utf-8") as f:
                    yaml.dump(
                        full_data,
                        f,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                        width=120,
                    )

            print(f"Created: {output_file}")

        except Exception as e:
            print(f"Error converting {lang_code}: {e}", file=sys.stderr)
            if not args.all:
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
