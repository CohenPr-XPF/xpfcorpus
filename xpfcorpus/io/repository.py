"""Package repository for bundled JSON data."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Optional

from ..engine.rules import LanguageData
from ..exceptions import LanguageNotFoundError
from .json_loader import JSONLoader
from .yaml_exporter import export_to_yaml


class PackageRepository:
    """
    Access bundled language data from the package.

    This uses importlib.resources to access JSON files
    bundled with the package.
    """

    _index: Optional[dict[str, dict]] = None

    @classmethod
    def _get_index(cls) -> dict[str, dict]:
        """Load and cache the language index."""
        if cls._index is None:
            try:
                # Python 3.9+ style
                files = resources.files("xpfcorpus.data")
                index_file = files.joinpath("index.json")
                content = index_file.read_text(encoding="utf-8")
                cls._index = json.loads(content)
            except (FileNotFoundError, AttributeError, TypeError):
                # Fallback: no bundled data yet
                cls._index = {}
        return cls._index

    @classmethod
    def available_languages(cls) -> dict[str, dict]:
        """
        Get a dictionary of available languages.

        Returns:
            Dict mapping language codes to metadata:
            {
                "es": {"scripts": ["latin"], "default": "latin"},
                "tt": {"scripts": ["latin", "cyrillic"], "default": null},
                ...
            }
        """
        return cls._get_index().copy()

    @classmethod
    def has_language(cls, code: str) -> bool:
        """
        Check if a language is available.

        Checks both the index and the filesystem for language files.
        This allows variants (e.g., es-ES.json) to exist without being in index.json.
        """
        # First check the index
        if code in cls._get_index():
            return True

        # Also check if the file exists (for variants not in index)
        try:
            files = resources.files("xpfcorpus.data.languages")
            lang_file = files.joinpath(f"{code}.json")
            # Try to read to check if it exists
            _ = lang_file.read_text(encoding="utf-8")
            return True
        except (FileNotFoundError, AttributeError, TypeError):
            return False

    @classmethod
    def get_scripts(cls, code: str) -> list[str]:
        """
        Get available scripts for a language.

        Raises:
            LanguageNotFoundError: If the language is not available.
        """
        index = cls._get_index()
        if code not in index:
            raise LanguageNotFoundError(code, list(index.keys()))
        return index[code].get("scripts", [])

    @classmethod
    def get_default_script(cls, code: str) -> Optional[str]:
        """
        Get the default script for a language.

        Returns None if no default is set.

        Raises:
            LanguageNotFoundError: If the language is not available.
        """
        index = cls._get_index()
        if code not in index:
            raise LanguageNotFoundError(code, list(index.keys()))
        return index[code].get("default")

    @classmethod
    @lru_cache(maxsize=128)
    def load_language(cls, code: str) -> LanguageData:
        """
        Load language data from the bundled JSON files.

        Args:
            code: Language code (e.g., "es", "tt").

        Returns:
            LanguageData object.

        Raises:
            LanguageNotFoundError: If the language is not available.
        """
        index = cls._get_index()
        if code not in index:
            raise LanguageNotFoundError(code, list(index.keys()))

        try:
            files = resources.files("xpfcorpus.data.languages")
            lang_file = files.joinpath(f"{code}.json")
            content = lang_file.read_text(encoding="utf-8")
            data = json.loads(content)

            # Ensure code is set in metadata
            if "metadata" not in data:
                data["metadata"] = {}
            if "code" not in data["metadata"]:
                data["metadata"]["code"] = code

            # Add default_script from index if not in file
            if "default_script" not in data["metadata"]:
                data["metadata"]["default_script"] = index[code].get("default")

            return JSONLoader.from_dict(data)

        except (FileNotFoundError, AttributeError, TypeError) as e:
            raise LanguageNotFoundError(code) from e

    @classmethod
    def export_language_yaml(cls, code: str) -> str:
        """
        Export a language's data as a YAML string.

        Args:
            code: Language code.

        Returns:
            YAML-formatted string.
        """
        lang_data = cls.load_language(code)
        return export_to_yaml(lang_data)

    @classmethod
    def clear_cache(cls):
        """Clear the loaded language cache."""
        cls._index = None
        cls.load_language.cache_clear()
