"""Legacy format loader for .rules and .verify files."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import TextIO

from ..engine.rules import RuleSet, ScriptData, SubRule, VerifyEntry
from ..exceptions import RulesParseError


def _sniff_dialect(filestream: TextIO) -> tuple[list[str], csv.Dialect]:
    """
    Determine the CSV dialect of a file.

    Returns (lines, dialect) where lines excludes comments and empty lines.
    """
    lines = [
        line for line in filestream
        if not (line.startswith("#") or len(line.strip()) == 0)
    ]

    if all(line.find("\t") >= 0 for line in lines):
        dialect = csv.get_dialect("excel-tab")
    else:
        sample = "\n".join(lines)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.get_dialect("excel")

    return lines, dialect


class LegacyLoader:
    """Load language data from .rules and .verify files."""

    @classmethod
    def load_rules(cls, path: Path | str) -> RuleSet:
        """
        Load rules from a .rules file.

        Args:
            path: Path to the .rules file.

        Returns:
            RuleSet object.
        """
        path = Path(path)
        if not path.exists():
            raise RulesParseError(str(path), "File not found")

        classes: dict[str, str] = {}
        pre: dict[str, str] = {}
        matches: dict[str, str] = {}
        subs: list[SubRule] = []
        ipasubs: list[SubRule] = []
        words: dict[str, list[str]] = {}

        with open(path, "r", encoding="utf-8") as f:
            lines, dialect = _sniff_dialect(f)

        reader = csv.DictReader(lines, dialect=dialect)

        for row in reader:
            try:
                rule_type = row.get("type", "").strip()

                if rule_type == "class":
                    sfrom = row.get("sfrom", "")
                    sto = row.get("sto", "")
                    classes[sfrom] = sto

                elif rule_type == "pre":
                    sfrom = row.get("sfrom", "")
                    sto = row.get("sto", "")
                    # Pre rules map character-to-character
                    for i, char in enumerate(sfrom):
                        if i < len(sto):
                            pre[char] = sto[i]

                elif rule_type == "match":
                    sfrom = row.get("sfrom", "")
                    sto = row.get("sto", "")
                    # Expand class references
                    while re.search(r"\{.*\}", sto):
                        sto = sto.format(**classes)
                    matches[sfrom] = sto

                elif rule_type == "sub":
                    sub = cls._parse_sub_rule(row, classes)
                    subs.append(sub)

                elif rule_type == "ipasub":
                    sub = cls._parse_sub_rule(row, classes)
                    ipasubs.append(sub)

                elif rule_type == "word":
                    word = row.get("sfrom", "")
                    sto = row.get("sto", "")
                    words[word] = sto.split()

            except Exception:
                # Skip malformed rules
                continue

        return RuleSet(
            classes=classes,
            pre=pre,
            matches=matches,
            subs=subs,
            ipasubs=ipasubs,
            words=words,
        )

    @classmethod
    def _parse_sub_rule(
        cls, row: dict[str, str], classes: dict[str, str]
    ) -> SubRule:
        """Parse a sub/ipasub rule from a CSV row."""
        sfrom = row.get("sfrom", "")
        sto = row.get("sto", "")
        precede = row.get("precede", "")
        follow = row.get("follow", "")
        weight_str = row.get("weight", "1.0")

        # Parse weight
        try:
            weight = float(weight_str) if weight_str else 1.0
        except ValueError:
            weight = 1.0

        # Expand class references
        for _ in range(10):  # Limit iterations to prevent infinite loops
            changed = False
            if re.search(r"\{.*\}", sfrom):
                sfrom = sfrom.format(**classes)
                changed = True
            if re.search(r"\{.*\}", sto):
                sto = sto.format(**classes)
                changed = True
            if re.search(r"\{.*\}", precede):
                precede = precede.format(**classes)
                changed = True
            if re.search(r"\{.*\}", follow):
                follow = follow.format(**classes)
                changed = True
            if not changed:
                break

        return SubRule(
            sfrom=sfrom,
            sto=sto,
            weight=weight,
            precede=precede,
            follow=follow,
        )

    @classmethod
    def load_verify(cls, path: Path | str) -> list[VerifyEntry]:
        """
        Load verification entries from a .verify file.

        Args:
            path: Path to the .verify or .verify.csv file.

        Returns:
            List of VerifyEntry objects.
        """
        path = Path(path)
        if not path.exists():
            return []

        entries: list[VerifyEntry] = []

        with open(path, "r", encoding="utf-8") as f:
            lines, dialect = _sniff_dialect(f)

        reader = csv.reader(lines, dialect=dialect)

        for row in reader:
            if len(row) < 2:
                continue

            word = row[0].strip()
            phonemes = row[1].strip()
            comment = row[2].strip() if len(row) > 2 else ""

            if word and phonemes:
                entries.append(VerifyEntry(
                    word=word,
                    phonemes=phonemes,
                    comment=comment,
                ))

        return entries

    @classmethod
    def load_from_files(
        cls,
        rules_path: Path | str,
        verify_path: Path | str | None = None,
    ) -> ScriptData:
        """
        Load script data from .rules and .verify files.

        Args:
            rules_path: Path to the .rules file.
            verify_path: Path to the .verify file (optional).

        Returns:
            ScriptData object.
        """
        rules = cls.load_rules(rules_path)

        verify: list[VerifyEntry] = []
        if verify_path:
            verify = cls.load_verify(verify_path)

        return ScriptData(rules=rules, verify=verify)
