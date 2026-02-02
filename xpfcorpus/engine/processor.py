"""Transcription processor - the core algorithm adapted from translate04.py."""

from __future__ import annotations

import re
from typing import Optional

from .rules import RuleSet, SubRule, VerifyEntry


class TranscriptionProcessor:
    """
    Core transcription engine that converts graphemes to phonemes.

    This is a pure transcription class with no I/O operations.
    The algorithm is adapted from XPF Corpus's translate04.py.
    """

    def __init__(self, rules: RuleSet, missing: str = "@"):
        """
        Initialize the processor with a rule set.

        Args:
            rules: The RuleSet containing all transcription rules.
            missing: Character to use for untranscribable graphemes.
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

        # Build pre-transcription table
        self._pre_table = rules.get_pre_translation_table()

    def transcribe(self, word: str) -> list[str]:
        """
        Transcribe a word from graphemes to phonemes.

        Args:
            word: The word to transcribe.

        Returns:
            List of phoneme strings.
        """
        # Check for whole-word exceptions
        if word in self.rules.words:
            return self.rules.words[word].copy()

        # Preprocess: apply pre-transcription and lowercase
        source = word.translate(self._pre_table).lower()

        # Process character by character
        source_chars = list(source)
        target_list: list[str] = []

        for idx, char in enumerate(source_chars):
            # If there's a direct match rule, use it (skip regex matching)
            if char in self._matches:
                transcription = self._matches[char]
            else:
                # Prepare context for rule matching
                precede = source[:idx]
                follow = source[idx + 1:]

                # Find all matching rules with their weights
                transcriptions = []
                for rule in self.rules.subs:
                    weight = rule.matches(char, precede, follow)
                    if weight is not None:
                        transcriptions.append((weight, rule.substitute(char)))

                # Choose the highest-weight transcription
                if transcriptions:
                    transcription = sorted(transcriptions)[-1][1]
                else:
                    transcription = self.missing

            # Skip empty transcriptions
            if transcription:
                target_list.append(transcription)

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
        Verify transcription against expected outputs.

        Args:
            entries: List of VerifyEntry objects with word/phonemes pairs.
            stop_on_first: If True, stop at the first failure.

        Returns:
            Tuple of (all_passed, list_of_error_messages).
        """
        errors: list[str] = []

        for entry in entries:
            transcribed = self.transcribe(entry.word)
            transcribed_str = " ".join(transcribed)
            expected = entry.phonemes

            if transcribed_str != expected:
                error_msg = (
                    f"'{entry.word}' -> '{transcribed_str}' "
                    f"(expected: '{expected}')"
                )
                errors.append(error_msg)

                if stop_on_first:
                    return False, errors

        return len(errors) == 0, errors
