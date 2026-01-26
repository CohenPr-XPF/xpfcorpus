"""JSON format loader for xpfcorpus - no external dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..engine.rules import (
    LanguageData,
    RuleSet,
    ScriptData,
    SubRule,
    VerifyEntry,
)


class JSONLoader:
    """Load language data from JSON files."""

    @classmethod
    def load(cls, path: Path | str) -> LanguageData:
        """
        Load language data from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            LanguageData object.
        """
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def load_string(cls, content: str) -> LanguageData:
        """Load language data from a JSON string."""
        data = json.loads(content)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LanguageData:
        """
        Convert a dictionary to LanguageData.

        Expected structure:
        {
            "metadata": {
                "code": "es",
                "name": "Spanish",
                "family": "...",
                "macroarea": "...",
                "compromised": false,
                "default_script": "latin"
            },
            "scripts": {
                "latin": {
                    "verify": [...],
                    "rules": {...}
                }
            }
        }
        """
        metadata = data.get("metadata", {})

        scripts: dict[str, ScriptData] = {}
        for script_name, script_data in data.get("scripts", {}).items():
            scripts[script_name] = cls._parse_script_data(
                script_data, metadata.get("classes", {})
            )

        return LanguageData(
            code=metadata.get("code", ""),
            name=metadata.get("name", ""),
            family=metadata.get("family", ""),
            macroarea=metadata.get("macroarea", ""),
            compromised=metadata.get("compromised"),
            default_script=metadata.get("default_script"),
            scripts=scripts,
        )

    @classmethod
    def _parse_script_data(
        cls, data: dict[str, Any], global_classes: dict[str, str]
    ) -> ScriptData:
        """Parse a script's rules and verify data."""
        rules_data = data.get("rules", {})
        verify_data = data.get("verify", [])

        # Parse verify entries
        verify_entries = [
            VerifyEntry(
                word=v.get("word", ""),
                phonemes=v.get("phonemes", ""),
                comment=v.get("comment", ""),
            )
            for v in verify_data
        ]

        # Parse rules
        rules = cls._parse_rules(rules_data, global_classes)

        return ScriptData(rules=rules, verify=verify_entries)

    @classmethod
    def _parse_rules(
        cls, data: dict[str, Any], global_classes: dict[str, str]
    ) -> RuleSet:
        """Parse rules from a dictionary."""
        # Merge global classes with script-specific classes
        classes = {**global_classes, **data.get("classes", {})}

        # Parse pre rules
        pre: dict[str, str] = {}
        for p in data.get("pre", []):
            sfrom = p.get("from", "")
            sto = p.get("to", "")
            # Pre rules map character-to-character
            for i, char in enumerate(sfrom):
                if i < len(sto):
                    pre[char] = sto[i]

        # Parse match rules (simple character mappings)
        matches: dict[str, str] = {}
        for m in data.get("match", []):
            sfrom = m.get("from", "")
            sto = m.get("to", "")
            # Expand class references
            while re.search(r"\{.*\}", sto):
                sto = sto.format(**classes)
            matches[sfrom] = sto

        # Parse sub rules
        subs = [
            cls._parse_sub_rule(s, classes)
            for s in data.get("sub", [])
        ]

        # Parse ipasub rules
        ipasubs = [
            cls._parse_sub_rule(s, classes)
            for s in data.get("ipasub", [])
        ]

        # Parse word rules
        words: dict[str, list[str]] = {}
        for w in data.get("word", []):
            word = w.get("word", "")
            phonemes = w.get("phonemes", "")
            words[word] = phonemes.split()

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
        cls, data: dict[str, Any], classes: dict[str, str]
    ) -> SubRule:
        """Parse a single sub rule, expanding class references."""
        sfrom = data.get("from", "")
        sto = data.get("to", "")
        precede = data.get("precede", "")
        follow = data.get("follow", "")
        weight = float(data.get("weight", 1.0))

        # Expand class references
        for field in [sfrom, sto, precede, follow]:
            while re.search(r"\{.*\}", field):
                field = field.format(**classes)

        # Re-expand after the loop (variables are local)
        while re.search(r"\{.*\}", sfrom):
            sfrom = sfrom.format(**classes)
        while re.search(r"\{.*\}", sto):
            sto = sto.format(**classes)
        while re.search(r"\{.*\}", precede):
            precede = precede.format(**classes)
        while re.search(r"\{.*\}", follow):
            follow = follow.format(**classes)

        return SubRule(
            sfrom=sfrom,
            sto=sto,
            weight=weight,
            precede=precede,
            follow=follow,
        )
