"""High-level Translator facade for xpfcorpus."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .engine.processor import TranslationProcessor
from .engine.rules import LanguageData, ScriptData
from .exceptions import (
    LanguageNotFoundError,
    ScriptNotFoundError,
    ScriptRequiredError,
    VerificationError,
)
from .io.legacy_loader import LegacyLoader
from .io.repository import PackageRepository


class Translator:
    """
    High-level grapheme-to-phoneme translator.

    Supports multiple data sources:
    - Package repository (default): bundled JSON data
    - External YAML file: custom language definitions
    - Legacy format: .rules and .verify files

    Examples:
        # Basic usage - language with default script
        >>> es = Translator("es")
        >>> es.translate("ejemplo")
        ['e', 'x', 'e', 'm', 'p', 'l', 'o']

        # Explicit script
        >>> tt = Translator("tt", "cyrillic")

        # External YAML file
        >>> custom = Translator("custom", yaml_file="my_lang.yaml")

        # Legacy format
        >>> legacy = Translator("test", rules_file="es.rules")
    """

    def __init__(
        self,
        language: str,
        script: Optional[str] = None,
        *,
        verify: bool = True,
        yaml_file: Optional[Path | str] = None,
        rules_file: Optional[Path | str] = None,
        verify_file: Optional[Path | str] = None,
    ):
        """
        Initialize a Translator for a language.

        Args:
            language: Language code (e.g., "es", "tt", "aak").
            script: Script to use (e.g., "latin", "cyrillic").
                    Required for multi-script languages without a default.
            verify: If True, verify the rules on initialization.
                    Raises VerificationError if verification fails.
            yaml_file: Path to an external YAML file (requires PyYAML).
            rules_file: Path to a legacy .rules file.
            verify_file: Path to a legacy .verify file.
        """
        self._language = language
        self._script: Optional[str] = None
        self._lang_data: Optional[LanguageData] = None
        self._script_data: Optional[ScriptData] = None
        self._processor: Optional[TranslationProcessor] = None

        # Load data from the appropriate source
        if yaml_file is not None:
            self._load_from_yaml(yaml_file, script)
        elif rules_file is not None:
            self._load_from_legacy(rules_file, verify_file)
        else:
            self._load_from_repository(language, script)

        # Verify if requested
        if verify and self._script_data and self._script_data.verify:
            passed, errors = self._processor.verify(self._script_data.verify)
            if not passed:
                raise VerificationError(language, errors)

    def _load_from_yaml(
        self,
        yaml_file: Path | str,
        script: Optional[str],
    ) -> None:
        """Load from an external YAML file."""
        from .io.yaml_loader import YAMLLoader

        yaml_file = Path(yaml_file)
        self._lang_data = YAMLLoader.load(yaml_file)
        self._resolve_script(script)
        self._init_processor()

    def _load_from_legacy(
        self,
        rules_file: Path | str,
        verify_file: Optional[Path | str],
    ) -> None:
        """Load from legacy .rules/.verify files."""
        self._script_data = LegacyLoader.load_from_files(rules_file, verify_file)
        self._script = "default"
        self._init_processor()

    def _load_from_repository(
        self,
        language: str,
        script: Optional[str],
    ) -> None:
        """Load from the package repository."""
        if not PackageRepository.has_language(language):
            available = list(PackageRepository.available_languages().keys())
            raise LanguageNotFoundError(language, available)

        self._lang_data = PackageRepository.load_language(language)
        self._resolve_script(script)
        self._init_processor()

    def _resolve_script(self, script: Optional[str]) -> None:
        """Resolve the script to use from language data."""
        if self._lang_data is None:
            return

        available_scripts = list(self._lang_data.scripts.keys())

        if script is not None:
            # Explicit script requested
            if script not in self._lang_data.scripts:
                raise ScriptNotFoundError(
                    self._language, script, available_scripts
                )
            self._script = script
        elif self._lang_data.default_script is not None:
            # Use default script
            self._script = self._lang_data.default_script
        elif len(available_scripts) == 1:
            # Only one script available
            self._script = available_scripts[0]
        else:
            # No default, multiple scripts - must specify
            raise ScriptRequiredError(self._language, available_scripts)

        self._script_data = self._lang_data.scripts[self._script]

    def _init_processor(self) -> None:
        """Initialize the translation processor."""
        if self._script_data is not None:
            self._processor = TranslationProcessor(self._script_data.rules)

    def translate(self, word: str) -> list[str]:
        """
        Translate a word from graphemes to phonemes.

        Args:
            word: The word to translate.

        Returns:
            List of phoneme strings.
        """
        if self._processor is None:
            return []
        return self._processor.translate(word)

    def verify(self) -> tuple[bool, list[str]]:
        """
        Verify the loaded rules against the verification data.

        Returns:
            Tuple of (all_passed, list_of_error_messages).
        """
        if self._processor is None or self._script_data is None:
            return True, []
        return self._processor.verify(self._script_data.verify)

    @property
    def language(self) -> str:
        """The language code."""
        return self._language

    @property
    def script(self) -> Optional[str]:
        """The script being used."""
        return self._script

    @property
    def name(self) -> str:
        """The language name."""
        if self._lang_data is not None:
            return self._lang_data.name
        return ""

    @property
    def family(self) -> str:
        """The language family."""
        if self._lang_data is not None:
            return self._lang_data.family
        return ""

    @property
    def is_compromised(self) -> bool:
        """Whether this language has known issues."""
        if self._lang_data is not None:
            return self._lang_data.compromised is not None
        return False

    def __repr__(self) -> str:
        script_part = f", script={self._script!r}" if self._script else ""
        return f"Translator({self._language!r}{script_part})"


def available_languages() -> dict[str, dict]:
    """
    Get all available languages from the package repository.

    Returns:
        Dict mapping language codes to metadata:
        {
            "es": {"scripts": ["latin"], "default": "latin"},
            "tt": {"scripts": ["latin", "cyrillic"], "default": null},
            ...
        }
    """
    return PackageRepository.available_languages()
