# xpfcorpus Documentation

This directory contains the Sphinx documentation for xpfcorpus.

## Live Documentation

The documentation is hosted on Read the Docs:
**https://xpfcorpus.readthedocs.io/**

## Building Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Build HTML documentation
make html

# View the built documentation
# Output is in _build/html/index.html
```

## Files

- `conf.py` - Sphinx configuration
- `index.rst` - Main documentation page
- `quickstart.rst` - Quick start guide
- `api.rst` - API reference (auto-generated from docstrings)
- `cli.rst` - CLI command reference
- `requirements.txt` - Documentation dependencies for Read the Docs
- `Makefile` - Build automation

## Read the Docs Configuration

The `.readthedocs.yaml` file in the repository root configures automatic builds on Read the Docs. Documentation is rebuilt automatically on every push to GitHub.
