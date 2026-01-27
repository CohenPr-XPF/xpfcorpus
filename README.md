# xpfcorpus

A Python package for grapheme-to-phoneme translation based on the [XPF Corpus](https://cohenpr-xpf.github.io/XPF/).

## Installation

```bash
pip install xpfcorpus
```

## Python API

```python
from xpfcorpus import Translator, available_languages

# Basic usage - languages with a default script
es = Translator("es")
es.translate("ejemplo")  # ['e', 'x', 'e', 'm', 'p', 'l', 'o']

# Languages with multiple scripts require explicit script choice
tt_latin = Translator("tt", "latin")
tt_cyrillic = Translator("tt", "cyrillic")

# Skip verification on load
es = Translator("es", verify=False)

# List available languages
available_languages()
# {"es": {"scripts": ["latin"], "default": "latin"},
#  "tt": {"scripts": ["latin", "cyrillic"], "default": None}, ...}
```

## Command-Line Interface

```bash
# Translate words
xpfcorpus translate es ejemplo hola mundo

# Translate from file (extracts first word from each line)
xpfcorpus translate es -f words.txt

# Translate from stdin
echo -e "mundo\nbueno" | xpfcorpus translate es
cat words.txt | xpfcorpus translate es -f -

# Combine command-line words and file
xpfcorpus translate es ejemplo hola -f more_words.txt

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
@misc{xpf_corpus,
  title={The Cross-linguistic Phonological Frequencies (XPF) Corpus},
  author={Cohen Priva, Uriel and Gleason, Emily},
  year={2022},
  url={https://cohenpr-xpf.github.io/XPF/}
}
```

## License

MIT
