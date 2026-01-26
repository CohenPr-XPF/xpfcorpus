"""Command-line interface for xpfcorpus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .exceptions import XPFCorpusError
from .io.repository import PackageRepository
from .translator import Translator, available_languages


def cmd_translate(args: argparse.Namespace) -> int:
    """Translate words to phonemes."""
    try:
        # Determine data source
        yaml_file = Path(args.yaml) if args.yaml else None
        rules_file = Path(args.rules) if args.rules else None
        verify_file = Path(args.verify_file) if args.verify_file else None

        translator = Translator(
            args.language,
            args.script,
            verify=not args.no_verify,
            yaml_file=yaml_file,
            rules_file=rules_file,
            verify_file=verify_file,
        )

        for word in args.words:
            phonemes = translator.translate(word)
            if args.json:
                print(json.dumps({"word": word, "phonemes": phonemes}))
            else:
                print(f"{word}\t{' '.join(phonemes)}")

        return 0

    except XPFCorpusError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """List available languages."""
    languages = available_languages()

    if not languages:
        print("No languages available. Generate data files first.", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(languages, indent=2))
    else:
        # Pretty print
        print(f"Available languages: {len(languages)}")
        print()
        for code, info in sorted(languages.items()):
            scripts = info.get("scripts", [])
            default = info.get("default")
            scripts_str = ", ".join(scripts)
            default_str = f" (default: {default})" if default else ""
            print(f"  {code}: {scripts_str}{default_str}")

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export a language's YAML."""
    try:
        yaml_content = PackageRepository.export_language_yaml(args.language)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(yaml_content, encoding="utf-8")
            print(f"Exported to: {output_path}", file=sys.stderr)
        else:
            print(yaml_content)

        return 0

    except XPFCorpusError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify a language's rules."""
    try:
        if args.all:
            all_langs = available_languages()
            # Build list of (lang, script) pairs to verify
            to_verify: list[tuple[str, Optional[str]]] = []
            for lang, info in all_langs.items():
                scripts = info.get("scripts", [])
                default = info.get("default")
                if default:
                    # Has a default script, verify with default
                    to_verify.append((lang, None))
                else:
                    # No default, verify each script separately
                    for script in scripts:
                        to_verify.append((lang, script))
        else:
            to_verify = [(args.language, args.script)]

        all_passed = True
        results = []

        for lang, script in to_verify:
            try:
                # Load without verification to check manually
                translator = Translator(lang, script, verify=False)
                passed, errors = translator.verify()

                label = f"{lang}-{script}" if script else lang
                status = "PASS" if passed else "FAIL"
                results.append({
                    "language": lang,
                    "script": script,
                    "passed": passed,
                    "errors": errors,
                })

                if not passed:
                    all_passed = False

                if not args.quiet:
                    if args.json:
                        pass  # Will print all at once
                    else:
                        error_summary = f" ({len(errors)} errors)" if errors else ""
                        print(f"{label}: {status}{error_summary}")
                        if args.verbose and errors:
                            for err in errors[:5]:
                                print(f"  - {err}")
                            if len(errors) > 5:
                                print(f"  ... and {len(errors) - 5} more")

            except XPFCorpusError as e:
                all_passed = False
                label = f"{lang}-{script}" if script else lang
                results.append({
                    "language": lang,
                    "script": script,
                    "passed": False,
                    "error": str(e),
                })
                if not args.quiet and not args.json:
                    print(f"{label}: ERROR - {e}")

        if args.json:
            print(json.dumps(results, indent=2))

        if not args.quiet and not args.json:
            print()
            total = len(to_verify)
            passed_count = sum(1 for r in results if r.get("passed", False))
            print(f"Results: {passed_count}/{total} passed")

        return 0 if all_passed else 1

    except XPFCorpusError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="xpfcorpus",
        description="XPF Corpus grapheme-to-phoneme translator",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # translate command
    translate_parser = subparsers.add_parser(
        "translate",
        help="Translate words to phonemes",
    )
    translate_parser.add_argument(
        "language",
        help="Language code (e.g., 'es', 'tt')",
    )
    translate_parser.add_argument(
        "words",
        nargs="+",
        help="Words to translate",
    )
    translate_parser.add_argument(
        "-s", "--script",
        help="Script to use (e.g., 'latin', 'cyrillic')",
    )
    translate_parser.add_argument(
        "--yaml",
        metavar="FILE",
        help="Use external YAML file",
    )
    translate_parser.add_argument(
        "--rules",
        metavar="FILE",
        help="Use legacy .rules file",
    )
    translate_parser.add_argument(
        "--verify-file",
        metavar="FILE",
        help="Use legacy .verify file",
    )
    translate_parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verification",
    )
    translate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    translate_parser.set_defaults(func=cmd_translate)

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List available languages",
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    list_parser.set_defaults(func=cmd_list)

    # export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export a language's YAML",
    )
    export_parser.add_argument(
        "language",
        help="Language code to export",
    )
    export_parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Output file (default: stdout)",
    )
    export_parser.set_defaults(func=cmd_export)

    # verify command
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify a language's rules",
    )
    verify_parser.add_argument(
        "language",
        nargs="?",
        help="Language code to verify (required unless --all)",
    )
    verify_parser.add_argument(
        "-s", "--script",
        help="Script to verify (e.g., 'latin', 'cyrillic')",
    )
    verify_parser.add_argument(
        "--all",
        action="store_true",
        help="Verify all languages (all scripts for multi-script languages)",
    )
    verify_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show error details",
    )
    verify_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Only show summary",
    )
    verify_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    verify_parser.set_defaults(func=cmd_verify)

    args = parser.parse_args(argv)

    # Handle verify requiring either language or --all
    if args.command == "verify" and not args.all and not args.language:
        parser.error("verify requires a language code or --all")

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
