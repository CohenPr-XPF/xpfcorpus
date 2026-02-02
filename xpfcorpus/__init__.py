"""
xpfcorpus - XPF Corpus grapheme-to-phoneme transcriber

A Python package for grapheme-to-phoneme transcription based on the XPF Corpus.

Example usage:
    >>> from xpfcorpus import Transcriber, available_languages
    >>>
    >>> # Basic usage - language with default script
    >>> es = Transcriber("es")
    >>> es.transcribe("ejemplo")
    ['e', 'x', 'e', 'm', 'p', 'l', 'o']
    >>>
    >>> # Multi-script language (requires explicit script)
    >>> tt = Transcriber("tt", "cyrillic")
    >>>
    >>> # List available languages
    >>> langs = available_languages()
    >>> "es" in langs
    True
"""

from .translator import Transcriber, available_languages
from .exceptions import (
    XPFCorpusError,
    LanguageNotFoundError,
    ScriptNotFoundError,
    ScriptRequiredError,
    VerificationError,
)

__version__ = "0.1.0"

__all__ = [
    "Transcriber",
    "available_languages",
    "XPFCorpusError",
    "LanguageNotFoundError",
    "ScriptNotFoundError",
    "ScriptRequiredError",
    "VerificationError",
    "__version__",
]
