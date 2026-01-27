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

echo "Installing package..."
pip install -e . -q

echo "Running verification..."
xpfcorpus verify --all

echo "Done!"
