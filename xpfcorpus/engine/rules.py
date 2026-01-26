"""Data structures for xpfcorpus rules and language data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SubRule:
    """
    A substitution rule with pattern matching and context.

    Wraps a regex-based substitution with optional precede/follow context
    and a weight for rule prioritization.
    """
    sfrom: str
    sto: str
    weight: float = 1.0
    precede: str = ""
    follow: str = ""

    # Compiled regexes (computed on first use)
    _sfrom_re: Optional[re.Pattern] = field(default=None, repr=False, compare=False)
    _precede_re: Optional[re.Pattern] = field(default=None, repr=False, compare=False)
    _follow_re: Optional[re.Pattern] = field(default=None, repr=False, compare=False)

    @property
    def sfrom_re(self) -> re.Pattern:
        if self._sfrom_re is None:
            self._sfrom_re = re.compile(self.sfrom)
        return self._sfrom_re

    @property
    def precede_re(self) -> re.Pattern:
        if self._precede_re is None:
            self._precede_re = re.compile(self.precede + "$")
        return self._precede_re

    @property
    def follow_re(self) -> re.Pattern:
        if self._follow_re is None:
            self._follow_re = re.compile("^" + self.follow)
        return self._follow_re

    def matches(self, sfrom: str, precede: str, follow: str) -> Optional[float]:
        """
        Check if this rule matches the given context.

        Returns the rule weight if matched, None otherwise.
        """
        if (self.sfrom_re.match(sfrom) and
            self.precede_re.search(precede) and
            self.follow_re.search(follow)):
            return self.weight
        return None

    def substitute(self, text: str) -> str:
        """Apply this rule's substitution to the given text."""
        return self.sfrom_re.sub(self.sto, text)

    def __lt__(self, other: SubRule) -> bool:
        if not isinstance(other, SubRule):
            raise TypeError(f"Cannot compare SubRule with {type(other)}")
        return self.weight < other.weight


@dataclass
class RuleSet:
    """
    A complete set of rules for translating a script.

    Contains:
    - classes: character class definitions for use in other rules
    - pre: character-level preprocessing (as a translation table)
    - matches: simple character-to-phoneme mappings (no context)
    - subs: context-sensitive substitution rules
    - ipasubs: post-processing substitution rules on IPA output
    - words: whole-word exception mappings
    """
    classes: dict[str, str] = field(default_factory=dict)
    pre: dict[str, str] = field(default_factory=dict)  # sfrom -> sto for maketrans
    matches: dict[str, str] = field(default_factory=dict)
    subs: list[SubRule] = field(default_factory=list)
    ipasubs: list[SubRule] = field(default_factory=list)
    words: dict[str, list[str]] = field(default_factory=dict)

    def get_pre_translation_table(self) -> dict[int, str]:
        """Build a str.maketrans table from the pre rules."""
        if not self.pre:
            return str.maketrans("", "")
        # Combine all pre mappings
        sfrom = "".join(self.pre.keys())
        sto = "".join(self.pre.values())
        return str.maketrans(sfrom, sto)


@dataclass
class VerifyEntry:
    """A single verification entry: word and expected phonemes."""
    word: str
    phonemes: str
    comment: str = ""


@dataclass
class ScriptData:
    """Data for a single script of a language."""
    rules: RuleSet
    verify: list[VerifyEntry] = field(default_factory=list)


@dataclass
class LanguageData:
    """
    Complete data for a language, including all scripts.

    A language may have multiple scripts (e.g., tt-latin, tt-cyrillic).
    If there's a default_script, that script is used when no script
    is explicitly specified.
    """
    code: str
    name: str = ""
    family: str = ""
    macroarea: str = ""
    compromised: Optional[dict | bool] = None
    default_script: Optional[str] = None
    scripts: dict[str, ScriptData] = field(default_factory=dict)

    def get_script_data(self, script: Optional[str] = None) -> ScriptData:
        """
        Get the ScriptData for the specified script, or the default.

        Raises ValueError if no script specified and no default exists.
        """
        if script is None:
            if self.default_script is None:
                available = list(self.scripts.keys())
                raise ValueError(
                    f"Language '{self.code}' has no default script; "
                    f"specify one of: {', '.join(available)}"
                )
            script = self.default_script

        if script not in self.scripts:
            available = list(self.scripts.keys())
            raise ValueError(
                f"Script '{script}' not found for language '{self.code}'; "
                f"available scripts: {', '.join(available)}"
            )

        return self.scripts[script]
