"""YAML export for xpfcorpus - pure Python, no PyYAML needed."""

from __future__ import annotations

from ..engine.rules import LanguageData, RuleSet, ScriptData, VerifyEntry


def _escape_yaml_string(s: str) -> str:
    """Escape a string for safe YAML output."""
    if not s:
        return '""'
    # Check if quoting is needed
    needs_quotes = (
        s.startswith((" ", "\t", "-", ":", "#", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`", "[", "]", "{", "}"))
        or s.endswith((" ", "\t"))
        or any(c in s for c in (":", "#", "{", "}", "[", "]", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`", "\n"))
        or s.lower() in ("true", "false", "null", "yes", "no", "on", "off")
        or _looks_like_number(s)
    )

    if needs_quotes:
        # Use single quotes, escape any single quotes inside
        escaped = s.replace("'", "''")
        return f"'{escaped}'"
    return s


def _looks_like_number(s: str) -> bool:
    """Check if a string looks like a number in YAML."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _indent(text: str, level: int) -> str:
    """Indent each line of text by the given level (2 spaces per level)."""
    prefix = "  " * level
    lines = text.split("\n")
    return "\n".join(prefix + line if line else line for line in lines)


def export_to_yaml(lang_data: LanguageData) -> str:
    """
    Export LanguageData to a YAML string.

    This uses pure Python string formatting - no PyYAML needed.

    Args:
        lang_data: The language data to export.

    Returns:
        YAML-formatted string.
    """
    lines: list[str] = []

    # Metadata section
    lines.append("metadata:")
    lines.append(f"  code: {_escape_yaml_string(lang_data.code)}")
    if lang_data.name:
        lines.append(f"  name: {_escape_yaml_string(lang_data.name)}")
    if lang_data.family:
        lines.append(f"  family: {_escape_yaml_string(lang_data.family)}")
    if lang_data.macroarea:
        lines.append(f"  macroarea: {_escape_yaml_string(lang_data.macroarea)}")
    if lang_data.compromised is not None:
        if isinstance(lang_data.compromised, bool):
            lines.append(f"  compromised: {str(lang_data.compromised).lower()}")
        elif isinstance(lang_data.compromised, dict):
            lines.append("  compromised:")
            for k, v in lang_data.compromised.items():
                lines.append(f"    {k}: {_escape_yaml_string(str(v))}")
    if lang_data.default_script:
        lines.append(f"  default_script: {_escape_yaml_string(lang_data.default_script)}")

    # Scripts section
    lines.append("")
    lines.append("scripts:")

    for script_name, script_data in lang_data.scripts.items():
        lines.append(f"  {_escape_yaml_string(script_name)}:")
        lines.extend(_export_script_data(script_data, indent_level=2))

    return "\n".join(lines) + "\n"


def _export_script_data(script_data: ScriptData, indent_level: int = 0) -> list[str]:
    """Export a script's data to YAML lines."""
    prefix = "  " * indent_level
    lines: list[str] = []

    # Verify section
    if script_data.verify:
        lines.append(f"{prefix}verify:")
        for entry in script_data.verify:
            lines.append(f"{prefix}  - word: {_escape_yaml_string(entry.word)}")
            lines.append(f"{prefix}    phonemes: {_escape_yaml_string(entry.phonemes)}")
            if entry.comment:
                lines.append(f"{prefix}    comment: {_escape_yaml_string(entry.comment)}")

    # Rules section
    lines.append(f"{prefix}rules:")
    rules_lines = _export_rules(script_data.rules, indent_level + 1)
    lines.extend(rules_lines)

    return lines


def _export_rules(rules: RuleSet, indent_level: int) -> list[str]:
    """Export a RuleSet to YAML lines."""
    prefix = "  " * indent_level
    lines: list[str] = []

    # Classes
    if rules.classes:
        lines.append(f"{prefix}classes:")
        for name, value in rules.classes.items():
            lines.append(f"{prefix}  {_escape_yaml_string(name)}: {_escape_yaml_string(value)}")

    # Pre rules
    if rules.pre:
        lines.append(f"{prefix}pre:")
        # Group pre rules by their original entry
        sfrom = "".join(rules.pre.keys())
        sto = "".join(rules.pre.values())
        lines.append(f"{prefix}  - from: {_escape_yaml_string(sfrom)}")
        lines.append(f"{prefix}    to: {_escape_yaml_string(sto)}")

    # Match rules
    if rules.matches:
        lines.append(f"{prefix}match:")
        for sfrom, sto in rules.matches.items():
            lines.append(f"{prefix}  - from: {_escape_yaml_string(sfrom)}")
            lines.append(f"{prefix}    to: {_escape_yaml_string(sto)}")

    # Sub rules
    if rules.subs:
        lines.append(f"{prefix}sub:")
        for sub in rules.subs:
            lines.append(f"{prefix}  - from: {_escape_yaml_string(sub.sfrom)}")
            lines.append(f"{prefix}    to: {_escape_yaml_string(sub.sto)}")
            if sub.weight != 1.0:
                lines.append(f"{prefix}    weight: {sub.weight}")
            if sub.precede:
                lines.append(f"{prefix}    precede: {_escape_yaml_string(sub.precede)}")
            if sub.follow:
                lines.append(f"{prefix}    follow: {_escape_yaml_string(sub.follow)}")

    # IPA sub rules
    if rules.ipasubs:
        lines.append(f"{prefix}ipasub:")
        for sub in rules.ipasubs:
            lines.append(f"{prefix}  - from: {_escape_yaml_string(sub.sfrom)}")
            lines.append(f"{prefix}    to: {_escape_yaml_string(sub.sto)}")
            if sub.weight != 1.0:
                lines.append(f"{prefix}    weight: {sub.weight}")
            if sub.precede:
                lines.append(f"{prefix}    precede: {_escape_yaml_string(sub.precede)}")
            if sub.follow:
                lines.append(f"{prefix}    follow: {_escape_yaml_string(sub.follow)}")

    # Word rules
    if rules.words:
        lines.append(f"{prefix}word:")
        for word, phonemes in rules.words.items():
            lines.append(f"{prefix}  - word: {_escape_yaml_string(word)}")
            lines.append(f"{prefix}    phonemes: {_escape_yaml_string(' '.join(phonemes))}")

    return lines
