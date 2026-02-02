"""High-level Transcriber facade for xpfcorpus."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .engine.processor import TranscriptionProcessor
from .engine.rules import LanguageData, ScriptData
from .exceptions import (
    LanguageNotFoundError,
    ScriptNotFoundError,
    ScriptRequiredError,
    VerificationError,
)
from .io.language_code import parse_language_code
from .io.legacy_loader import LegacyLoader
from .io.repository import PackageRepository


class Transcriber:
    """
    High-level grapheme-to-phoneme transcriber.

    Supports multiple data sources:
    - Package repository (default): bundled JSON data
    - External YAML file: custom language definitions
    - Legacy format: .rules and .verify files

    Examples:
        # Basic usage - language with default script
        >>> es = Transcriber("es")
        >>> es.transcribe("ejemplo")
        ['e', 'x', 'e', 'm', 'p', 'l', 'o']

        # Explicit script
        >>> tt = Transcriber("tt", "cyrillic")

        # External YAML file
        >>> custom = Transcriber("custom", yaml_file="my_lang.yaml")

        # Legacy format
        >>> legacy = Transcriber("test", rules_file="es.rules")
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
        Initialize a Transcriber for a language.

        Args:
            language: Language code (e.g., "es", "tt", "aak").
                     Supports BCP-47 style codes with script and region:
                     - "es-ES" (region preserved, treated as variant)
                     - "yi-Latn" (script extracted)
                     - "tt-cyrillic" (script extracted)
                     - "zh-Hans-CN" (script extracted, region preserved)
            script: Script to use (e.g., "latin", "cyrillic").
                    Required for multi-script languages without a default.
                    If provided, overrides any script in the language code.
            verify: If True, verify the rules on initialization.
                    Raises VerificationError if verification fails.
            yaml_file: Path to an external YAML file (requires PyYAML).
            rules_file: Path to a legacy .rules file.
            verify_file: Path to a legacy .verify file.
        """
        # Parse language code to extract language, script, and region
        parsed_lang, parsed_script, parsed_region = parse_language_code(language, script)

        # Use explicit script if provided, otherwise use parsed script
        effective_script = script if script is not None else parsed_script

        self._language = parsed_lang
        self._variant: Optional[str] = parsed_region  # Store variant (region code)
        self._original_code = language  # Store original for reference
        self._script: Optional[str] = None
        self._lang_data: Optional[LanguageData] = None
        self._script_data: Optional[ScriptData] = None
        self._processor: Optional[TranscriptionProcessor] = None

        # Load data from the appropriate source
        if yaml_file is not None:
            self._load_from_yaml(yaml_file, effective_script)
        elif rules_file is not None:
            self._load_from_legacy(rules_file, verify_file)
        else:
            self._load_from_repository(parsed_lang, effective_script, parsed_region)

        # Verify if requested
        if verify and self._script_data and self._script_data.verify:
            passed, errors = self._processor.verify(self._script_data.verify)
            if not passed:
                raise VerificationError(parsed_lang, errors)

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
        region: Optional[str] = None,
    ) -> None:
        """
        Load from the package repository.

        Tries to load variant-specific file (e.g., es-ES.json) first if region
        is provided, then falls back to base language (e.g., es.json) with a warning.
        When falling back, sets self._variant to None.
        """
        import warnings

        # Try to load variant first if region is specified
        if region is not None:
            variant_code = f"{language}-{region}"
            if PackageRepository.has_language(variant_code):
                self._lang_data = PackageRepository.load_language(variant_code)
                self._resolve_script(script)
                self._init_processor()
                # Variant successfully loaded, keep self._variant as-is
                return

            # Variant not found, fall back to base language with warning
            warnings.warn(
                f"Language variant '{variant_code}' not found. "
                f"Falling back to base language '{language}'. "
                f"To create a variant, add {variant_code}.json to the data/languages directory.",
                UserWarning,
                stacklevel=3
            )
            # Clear variant since we're falling back to base language
            self._variant = None

        # Load base language
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
        """Initialize the transcription processor."""
        if self._script_data is not None:
            self._processor = TranscriptionProcessor(self._script_data.rules)

    def transcribe(self, word: str) -> list[str]:
        """
        Transcribe a word from graphemes to phonemes.

        Args:
            word: The word to transcribe.

        Returns:
            List of phoneme strings.
        """
        if self._processor is None:
            return []
        return self._processor.transcribe(word)

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
    def variant(self) -> Optional[str]:
        """
        The language variant (region code) if a variant file was loaded.

        Returns:
            Region code (e.g., "ES", "MX") if variant file exists, otherwise None.

        Examples:
            >>> es = Transcriber("es")
            >>> es.variant  # None (base language)
            >>>
            >>> # If es-ES.json exists:
            >>> es_es = Transcriber("es-ES")
            >>> es_es.variant  # "ES"
            >>>
            >>> # If es-ES.json doesn't exist (falls back to es.json):
            >>> es_es = Transcriber("es-ES")
            >>> es_es.variant  # None
        """
        return self._variant

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
        return f"Transcriber({self._language!r}{script_part})"


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
