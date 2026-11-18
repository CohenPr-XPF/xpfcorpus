#!/bin/bash
# Sync xpfcorpus data from local XPF corpus
# Assumes XPF repo is at ../XPF relative to this script

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
XPF_DIR="${SCRIPT_DIR}/../XPF"

if [ ! -d "$XPF_DIR/Data" ]; then
    echo "Error: XPF corpus not found at $XPF_DIR"
    echo "Expected directory structure: ../XPF/Data/"
    exit 1
fi

echo "Syncing from: $XPF_DIR"

cd "$SCRIPT_DIR"

echo "Generating index.json..."
python3 convert_to_yaml.py --generate-index \
    "$XPF_DIR/Data/langs-list.tsv" "$XPF_DIR/Data" \
    > xpfcorpus/data/index.json

echo "Generating language JSON files..."
python3 convert_to_yaml.py --all --format json _ \
    "$XPF_DIR/Data/langs-list.tsv" "$XPF_DIR/Data" \
    xpfcorpus/data/languages

# Languages that do not come from XPF (he.json, written by import-he2ipa.py)
# are not in langs-list.tsv, so the generated index leaves them out. Keep an
# index entry for every language file there is.
echo "Re-adding languages imported from outside XPF to index.json..."
python3 - xpfcorpus/data <<'EOF'
import json, sys
from pathlib import Path
data = Path(sys.argv[1])
index = json.loads((data / "index.json").read_text(encoding="utf-8"))
for f in sorted((data / "languages").glob("*.json")):
    if f.stem not in index:
        d = json.loads(f.read_text(encoding="utf-8"))
        index[f.stem] = {"scripts": list(d["scripts"]),
                         "default": d.get("metadata", {}).get("default_script")}
        print(f"  {f.stem}")
(data / "index.json").write_text(
    json.dumps(index, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8")
EOF

echo "Installing package..."
pip install -e . -q

echo "Running verification..."
xpfcorpus verify --all

echo "Done!"
