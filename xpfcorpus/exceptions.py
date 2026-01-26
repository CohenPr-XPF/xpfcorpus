"""Custom exceptions for xpfcorpus."""


class XPFCorpusError(Exception):
    """Base exception for all xpfcorpus errors."""
    pass


class LanguageNotFoundError(XPFCorpusError):
    """Raised when a requested language is not available."""

    def __init__(self, code: str, available: list[str] | None = None):
        self.code = code
        self.available = available or []
        if self.available:
            msg = f"Language '{code}' not found. Available languages: {len(self.available)}"
        else:
            msg = f"Language '{code}' not found."
        super().__init__(msg)


class ScriptNotFoundError(XPFCorpusError):
    """Raised when a requested script is not available for a language."""

    def __init__(self, code: str, script: str, available: list[str]):
        self.code = code
        self.script = script
        self.available = available
        msg = (
            f"Script '{script}' not found for language '{code}'. "
            f"Available scripts: {', '.join(available)}"
        )
        super().__init__(msg)


class ScriptRequiredError(XPFCorpusError):
    """Raised when a language requires explicit script selection."""

    def __init__(self, code: str, available: list[str]):
        self.code = code
        self.available = available
        msg = (
            f"Language '{code}' has no default script; "
            f"specify one of: {', '.join(available)}"
        )
        super().__init__(msg)


class VerificationError(XPFCorpusError):
    """Raised when language verification fails."""

    def __init__(self, code: str, errors: list[str]):
        self.code = code
        self.errors = errors
        error_count = len(errors)
        preview = errors[:3]
        msg = f"Verification failed for '{code}' with {error_count} error(s):\n"
        msg += "\n".join(f"  - {e}" for e in preview)
        if error_count > 3:
            msg += f"\n  ... and {error_count - 3} more"
        super().__init__(msg)


class RulesParseError(XPFCorpusError):
    """Raised when a rules file cannot be parsed."""

    def __init__(self, path: str, detail: str = ""):
        self.path = path
        self.detail = detail
        msg = f"Failed to parse rules file: {path}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)
