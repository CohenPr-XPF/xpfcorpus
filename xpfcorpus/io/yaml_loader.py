"""YAML format loader for xpfcorpus - requires PyYAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..engine.rules import LanguageData
from .json_loader import JSONLoader


def _check_pyyaml():
    """Check if PyYAML is installed, raise helpful error if not."""
    try:
        import yaml  # noqa: F401
        return True
    except ImportError:
        raise ImportError(
            "PyYAML is required to load YAML files. "
            "Install it with: pip install xpfcorpus[yaml] "
            "or: pip install pyyaml"
        )


class YAMLLoader:
    """
    Load language data from YAML files.

    Requires PyYAML to be installed. Install with:
        pip install xpfcorpus[yaml]
    or:
        pip install pyyaml
    """

    @classmethod
    def load(cls, path: Path | str) -> LanguageData:
        """
        Load language data from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            LanguageData object.

        Raises:
            ImportError: If PyYAML is not installed.
        """
        _check_pyyaml()
        import yaml

        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    @classmethod
    def load_string(cls, content: str) -> LanguageData:
        """Load language data from a YAML string."""
        _check_pyyaml()
        import yaml

        data = yaml.safe_load(content)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LanguageData:
        """
        Convert a dictionary to LanguageData.

        Uses the same format as JSONLoader, so we delegate to it.
        """
        return JSONLoader.from_dict(data)
