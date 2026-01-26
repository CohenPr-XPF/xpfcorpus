"""
xpfcorpus - XPF Corpus grapheme-to-phoneme translator

A Python package for grapheme-to-phoneme translation based on the XPF Corpus.

Example usage:
    >>> from xpfcorpus import Translator, available_languages
    >>>
    >>> # Basic usage - language with default script
    >>> es = Translator("es")
    >>> es.translate("ejemplo")
    ['e', 'x', 'e', 'm', 'p', 'l', 'o']
    >>>
    >>> # Multi-script language (requires explicit script)
    >>> tt = Translator("tt", "cyrillic")
    >>>
    >>> # List available languages
    >>> langs = available_languages()
    >>> "es" in langs
    True
"""

from .translator import Translator, available_languages
from .exceptions import (
    XPFCorpusError,
    LanguageNotFoundError,
    ScriptNotFoundError,
    ScriptRequiredError,
    VerificationError,
)

__version__ = "0.1.0"

__all__ = [
    "Translator",
    "available_languages",
    "XPFCorpusError",
    "LanguageNotFoundError",
    "ScriptNotFoundError",
    "ScriptRequiredError",
    "VerificationError",
    "__version__",
]
