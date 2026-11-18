#!/usr/bin/env python3
"""Import he2ipa's Hebrew rules (he.yaml) as xpfcorpus language data.

    python3 import-he2ipa.py path/to/he2ipa/he2ipa/rules/he.yaml [--out DIR]

Writes DIR/he.json (default: xpfcorpus/data/languages) and adds or updates
the "he" entry in the index.json next to that directory.

What the import changes, and nothing else:

* Rhotics: every rhotic symbol on the phoneme side (match/sub "to", every
  ipasub field, word and verify "phonemes") becomes U+1D1A (small capital
  inverted R), the corpus's symbol for the Hebrew rhotic, whatever he2ipa
  emits. Users who want another symbol add a final ipasub that replaces it
  unconditionally: a weight below every rule in the file, e.g.
  {from: "ᴚ", to: "ʁ", weight: 0}. IPA rhotics in comments are rewritten
  too, so comments and transcriptions agree. The same goes for /ħ/ and /ʕ/, which
  the rules keep: speakers who merge them (χ, ʔ or nothing) suppress them
  with final ipasubs in the same way.
* Metadata: marked compromised, with a note on what the spelling leaves
  undetermined (vocal vs silent shva, prefixes, qamats qatan).

Grapheme-side fields (match/sub "from", sub precede/follow, classes, pre)
are copied unchanged. The script prints every value it rewrites and stops
if a phoneme-side field still holds a rhotic afterwards.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

RHOTIC = "ᴚ"  # ᴚ LATIN LETTER SMALL CAPITAL TURNED R
# Rhotic symbols he2ipa might emit. Plain "r" is included: a Hebrew rule
# producing /r/ means the rhotic too.
RHOTICS = "ʁʀrɾɹɻɽ"
RHOTIC_RE = re.compile(f"[{RHOTICS}]")
# Comments are English prose, so only the IPA rhotics are rewritten there.
COMMENT_RHOTIC_RE = re.compile("[ʁʀɾɹɻɽ]")

NOTE = (
    "standard pointing does not mark whether a shva is pronounced (/e/) or "
    "silent; the rules decide it from the shape of the word, which is right "
    "for most words but not all (a meteg, U+05BD, forces a heard shva). "
    "Prefixes are recognized only when followed by | (as in \u05d5\u05bc|\u05de\u05b7\u05d9\u05b4\u05dd). "
    "Qamats qatan is read as /o/ only when written with U+05C7, before a "
    "hataf qamats, or in the stem \u05db\u05dc (kol); otherwise qamats is /a/."
)

# Phoneme-side fields per rule type. Everything else is grapheme side.
PHONEME_FIELDS = {
    "match": ("to",),
    "sub": ("to",),
    "ipasub": ("from", "to", "precede", "follow"),
    "word": ("phonemes",),
}


def convert(value, where, changes, pattern=RHOTIC_RE):
    if not isinstance(value, str) or not pattern.search(value):
        return value
    new = pattern.sub(RHOTIC, value)
    changes.append(f"  {where}: {value!r} -> {new!r}")
    return new


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("yaml_file", type=Path)
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).parent / "xpfcorpus/data/languages")
    args = ap.parse_args()

    data = yaml.safe_load(args.yaml_file.read_text(encoding="utf-8"))
    if data.get("metadata", {}).get("code") != "he":
        sys.exit(f"{args.yaml_file}: metadata.code is not 'he'")

    changes = []
    for sname, sdata in data["scripts"].items():
        rules = sdata.get("rules", {})
        for kind, fields in PHONEME_FIELDS.items():
            for i, rule in enumerate(rules.get(kind) or []):
                for f in fields:
                    if f in rule:
                        rule[f] = convert(rule[f], f"{sname}.{kind}[{i}].{f}", changes)
                if "comment" in rule:
                    rule["comment"] = convert(rule["comment"], f"{sname}.{kind}[{i}].comment",
                                              changes, COMMENT_RHOTIC_RE)
        for i, entry in enumerate(sdata.get("verify") or []):
            entry["phonemes"] = convert(entry["phonemes"], f"{sname}.verify[{i}]", changes)
            if "comment" in entry:
                entry["comment"] = convert(entry["comment"], f"{sname}.verify[{i}].comment",
                                           changes, COMMENT_RHOTIC_RE)

    # Nothing rhotic may survive on the phoneme side.
    left = [
        (s, kind, f, rule[f])
        for s, sd in data["scripts"].items()
        for kind, fields in PHONEME_FIELDS.items()
        for rule in (sd.get("rules", {}).get(kind) or [])
        for f in fields
        if isinstance(rule.get(f), str) and RHOTIC_RE.search(rule[f])
    ]
    if left:
        sys.exit(f"rhotics left after conversion: {left}")

    data["metadata"]["compromised"] = {"note": NOTE}

    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out / "he.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    index_file = args.out.parent / "index.json"
    index = json.loads(index_file.read_text(encoding="utf-8")) if index_file.exists() else {}
    # Keep the index's existing order (XPF languages, then the compromised
    # ones); a new entry goes at the end, an existing one is updated in place.
    index["he"] = {"scripts": list(data["scripts"]),
                   "default": data["metadata"].get("default_script")}
    index_file.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")

    print(f"wrote {out} and the 'he' entry of {index_file}")
    print(f"rhotics rewritten to {RHOTIC} ({len(changes)}):")
    print("\n".join(changes) if changes else "  none")


if __name__ == "__main__":
    main()
