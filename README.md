# xpfcorpus

A Python package for grapheme-to-phoneme translation based on the [XPF Corpus](https://cohenpr-xpf.github.io/XPF/).

## Installation

```bash
pip install xpfcorpus
```

## Usage

```python
from xpfcorpus import translator, available_languages

# List available languages
print(available_languages())  # ['aak', 'aau', 'ab', ..., 'yi-Latn', ...]

# Create a translator for a specific language
es = translator("es")

# Translate a word to phonemes
phonemes = es.translate("ejemplo")
print(phonemes)  # ['e', 'x', 'e', 'm', 'p', 'l', 'o']

# Languages with multiple scripts use hyphenated codes
tatar_latin = translator("tt-latn")
tatar_cyrillic = translator("tt-cyrillic")

# With verification (raises ValueError if verification fails)
es_verified = translator("es", verify=True)
```

## Supported Languages

The package includes rules for 207 language/script combinations across 140 language families. Some languages have multiple scripts:

- `iu-Latn`, `iu-Syll` (Inuktitut: Latin, Syllabics)
- `tt-latn`, `tt-cyrillic` (Tatar)
- `yi-Latn` (Yiddish in Latin script)

See `available_languages()` for the full list.

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
