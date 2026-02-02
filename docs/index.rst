xpfcorpus Documentation
========================

A Python package for grapheme-to-phoneme transcription based on the `XPF Corpus <https://cohenpr-xpf.github.io/XPF/>`_.

**XPF Resources:**

* `XPF Website <https://cohenpr-xpf.github.io/XPF/index.html>`_
* `XPF Manual (PDF) <https://cohenpr-xpf.github.io/XPF/manual/xpf_manual.pdf>`_
* `XPF GitHub Repository <https://github.com/CohenPr-XPF/XPF>`_

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   api
   cli

Installation
------------

.. code-block:: bash

   pip install xpfcorpus

Quick Example
-------------

.. code-block:: python

   from xpfcorpus import Transcriber

   # Basic usage
   es = Transcriber("es")
   result = es.transcribe("ejemplo")
   print(result)  # ['e', 'x', 'e', 'm', 'p', 'l', 'o']

Features
--------

* **201 languages** with 203 language/script combinations
* **Pure Python** with no required dependencies
* **BCP-47 language codes** support (e.g., "es-ES", "yi-Latn")
* **Multiple data sources**: bundled JSON, external YAML, or legacy formats
* **Command-line interface** for batch processing
* **100% verification** - all 203 language/script combinations pass verification tests

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
