"""Translation processor - the core algorithm adapted from translate04.py."""

from __future__ import annotations

import re
from typing import Optional

from .rules import RuleSet, SubRule, VerifyEntry


class TranslationProcessor:
    """
    Core translation engine that converts graphemes to phonemes.

    This is a pure translation class with no I/O operations.
    The algorithm is adapted from XPF Corpus's translate04.py.
    """

    def __init__(self, rules: RuleSet, missing: str = "@"):
        """
        Initialize the processor with a rule set.

        Args:
            rules: The RuleSet containing all translation rules.
            missing: Character to use for untranslatable graphemes.
        """
        self.rules = rules
        self.missing = missing

        # Expand class references in matches
        self._matches: dict[str, str] = {}
        for sfrom, sto in rules.matches.items():
            # Expand {class} references
            while re.search(r"\{.*\}", sto):
                sto = sto.format(**rules.classes)
            self._matches[sfrom] = sto

        # Build pre-translation table
        self._pre_table = rules.get_pre_translation_table()

    def translate(self, word: str) -> list[str]:
        """
        Translate a word from graphemes to phonemes.

        Args:
            word: The word to translate.

        Returns:
            List of phoneme strings.
        """
        # Check for whole-word exceptions
        if word in self.rules.words:
            return self.rules.words[word].copy()

        # Preprocess: apply pre-translation and lowercase
        source = word.translate(self._pre_table).lower()

        # Process character by character
        source_chars = list(source)
        target_list: list[str] = []

        for idx, char in enumerate(source_chars):
            # If there's a direct match rule, use it (skip regex matching)
            if char in self._matches:
                translation = self._matches[char]
            else:
                # Prepare context for rule matching
                precede = source[:idx]
                follow = source[idx + 1:]

                # Find all matching rules with their weights
                translations = []
                for rule in self.rules.subs:
                    weight = rule.matches(char, precede, follow)
                    if weight is not None:
                        translations.append((weight, rule.substitute(char)))

                # Choose the highest-weight translation
                if translations:
                    translation = sorted(translations)[-1][1]
                else:
                    translation = self.missing

            # Skip empty translations
            if translation:
                target_list.append(translation)

        # Join with spaces and apply IPA post-processing
        target_string = " ".join(target_list)

        # Apply ipasub rules in order of descending weight
        sorted_ipasubs = sorted(self.rules.ipasubs, key=lambda r: -r.weight)
        for rule in sorted_ipasubs:
            target_string = rule.substitute(target_string)

        return target_string.split()

    def verify(
        self,
        entries: list[VerifyEntry],
        *,
        stop_on_first: bool = False,
    ) -> tuple[bool, list[str]]:
        """
        Verify translation against expected outputs.

        Args:
            entries: List of VerifyEntry objects with word/phonemes pairs.
            stop_on_first: If True, stop at the first failure.

        Returns:
            Tuple of (all_passed, list_of_error_messages).
        """
        errors: list[str] = []

        for entry in entries:
            translated = self.translate(entry.word)
            translated_str = " ".join(translated)
            expected = entry.phonemes

            if translated_str != expected:
                error_msg = (
                    f"'{entry.word}' -> '{translated_str}' "
                    f"(expected: '{expected}')"
                )
                errors.append(error_msg)

                if stop_on_first:
                    return False, errors

        return len(errors) == 0, errors
