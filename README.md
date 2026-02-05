# xpfcorpus

[![Documentation Status](https://readthedocs.org/projects/xpfcorpus/badge/?version=latest)](https://xpfcorpus.readthedocs.io/en/latest/?badge=latest)

A Python package for grapheme-to-phoneme transcription based on the [XPF Corpus](https://cohenpr-xpf.github.io/XPF/).

**Documentation:** [xpfcorpus.readthedocs.io](https://xpfcorpus.readthedocs.io/)

**XPF Corpus Resources:**
- [XPF Website](https://cohenpr-xpf.github.io/XPF/index.html)
- [XPF Manual (PDF)](https://cohenpr-xpf.github.io/XPF/manual/xpf_manual.pdf)
- [XPF GitHub](https://github.com/CohenPr-XPF/XPF)

## Installation

```bash
pip install xpfcorpus
```

## Python API

```python
from xpfcorpus import Transcriber, available_languages

# Basic usage - languages with a default script
es = Transcriber("es")
es.transcribe("ejemplo")  # ['e', 'x', 'e', 'm', 'p', 'l', 'o']

# Languages with multiple scripts require explicit script choice
tt_latin = Transcriber("tt", "latin")
tt_cyrillic = Transcriber("tt", "cyrillic")

# BCP-47 style language codes with script/region
es_es = Transcriber("es-ES")  # Region code stripped, uses default script
yi = Transcriber("yi-Latn")   # Script extracted from code
tt = Transcriber("tt-cyrillic")  # Script name in code
zh = Transcriber("zh-Hans-CN")  # Script extracted, region stripped

# Explicit script parameter overrides code
yi = Transcriber("yi-Latn", script="hebrew")  # Uses hebrew, not latin

# Skip verification on load
es = Transcriber("es", verify=False)

# List available languages
available_languages()
# {"es": {"scripts": ["latin"], "default": "latin"},
#  "tt": {"scripts": ["latin", "cyrillic"], "default": None}, ...}
```

### Language Code Format

The package supports BCP-47 style language codes:

- **Simple codes**: `"es"`, `"tt"`, `"yi"`
- **With region** (variants): `"es-ES"`, `"en-US"` → treated as language variants
- **With script** (extracted): `"yi-Latn"`, `"tt-Cyrl"` → extracts script
- **Script names** (extracted): `"tt-cyrillic"`, `"yi-latin"` → extracts script
- **Complex codes**: `"zh-Hans-CN"` → extracts `"hans"` script, preserves `"CN"` region

When both a script in the code and an explicit `script` parameter are provided, the explicit parameter takes precedence.

### Language Variants

Region codes are treated as language variants. The package will:

1. Try to load variant-specific data (e.g., `es-ES.json`) if available
2. Fall back to base language (e.g., `es.json`) with a warning if variant not found
3. Store the variant information in the `variant` property (only if variant file exists)

```python
# Base language
es = Transcriber("es")
print(es.variant)  # None

# Variant request (falls back to base with warning if es-ES.json doesn't exist)
es_es = Transcriber("es-ES")
print(es_es.variant)  # None (because es-ES.json doesn't exist, fell back to es.json)

# If es-ES.json existed, then:
# es_es.variant would be "ES"
```

**Behavior:**
- If variant file exists: `variant` property returns the region code (e.g., "ES")
- If variant file doesn't exist: falls back to base language, `variant` is `None`

To create a variant, add a JSON file like `es-ES.json` to the `xpfcorpus/data/languages/` directory with variant-specific rules.

## Command-Line Interface

```bash
# Transcribe words
xpfcorpus transcribe es ejemplo hola mundo

# Transcribe from file (extracts first word from each line)
xpfcorpus transcribe es -f words.txt

# Transcribe from stdin
echo -e "mundo\nbueno" | xpfcorpus transcribe es
cat words.txt | xpfcorpus transcribe es -f -

# Combine command-line words and file
xpfcorpus transcribe es ejemplo hola -f more_words.txt

# List available languages
xpfcorpus list
xpfcorpus list --json

# Export language rules as YAML
xpfcorpus export es
xpfcorpus export es -o spanish.yaml

# Verify language rules
xpfcorpus verify es -v
xpfcorpus verify --all
```

## Supported Languages

The package includes rules for 201 languages with 203 language/script combinations. Some languages have multiple scripts:

- `iu` (Inuktitut): latin, syllabics
- `tt` (Tatar): latin, cyrillic

Use `xpfcorpus list` or `available_languages()` for the full list.

## Citation

If you use this package in your research, please cite the XPF Corpus:

```bibtex
@Manual{XPF2021manual,
  author={Cohen Priva, Uriel and Strand, Emily and Yang, Shiying and Mizgerd, William and Creighton, Abigail and Bai, Justin and Mathew, Rebecca and Shao, Allison and Schuster, Jordan and Wiepert, Daniela},
  title = 	 {The Cross-linguistic Phonological Frequencies (XPF) Corpus manual},
  year = 	 {2021},
  note =         {Accessible online, \url{https://cohenpr-xpf.github.io/XPF/manual/xpf_manual.pdf}}
}
```

## License

MIT
