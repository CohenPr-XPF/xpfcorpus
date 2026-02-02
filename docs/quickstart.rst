Quick Start Guide
=================

Installation
------------

Install xpfcorpus via pip:

.. code-block:: bash

   pip install xpfcorpus

For YAML support (optional):

.. code-block:: bash

   pip install xpfcorpus[yaml]

Basic Usage
-----------

Simple Transcription
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from xpfcorpus import Transcriber

   # Create a transcriber for Spanish
   es = Transcriber("es")

   # Transcribe a word
   result = es.transcribe("ejemplo")
   print(result)  # ['e', 'x', 'e', 'm', 'p', 'l', 'o']

Multi-Script Languages
~~~~~~~~~~~~~~~~~~~~~~

Some languages have multiple scripts and require explicit script selection:

.. code-block:: python

   from xpfcorpus import Transcriber

   # Tatar has both Latin and Cyrillic scripts
   tt_latin = Transcriber("tt", "latin")
   tt_cyrillic = Transcriber("tt", "cyrillic")

   # Without explicit script, this raises ScriptRequiredError
   # tt = Transcriber("tt")  # Error!

BCP-47 Language Codes
~~~~~~~~~~~~~~~~~~~~~

The package supports BCP-47 style language codes with script and region components:

.. code-block:: python

   from xpfcorpus import Transcriber

   # Region codes are stripped
   es_es = Transcriber("es-ES")  # Same as Transcriber("es")

   # Script codes are extracted (ISO 15924 format)
   yi = Transcriber("yi-Latn")   # Uses Latin script

   # Lowercase script names also work
   tt = Transcriber("tt-cyrillic")  # Uses Cyrillic script

   # Complex codes: script extracted, region stripped
   zh = Transcriber("zh-Hans-CN")  # Uses Hans script

   # Explicit script parameter overrides the code
   yi = Transcriber("yi-Latn", script="hebrew")  # Uses Hebrew, not Latin

Verification
~~~~~~~~~~~~

By default, rules are verified on load. You can skip verification:

.. code-block:: python

   from xpfcorpus import Transcriber

   # Skip verification for faster loading
   es = Transcriber("es", verify=False)

   # Manually verify later
   passed, errors = es.verify()
   if not passed:
       for error in errors:
           print(error)

Available Languages
~~~~~~~~~~~~~~~~~~~

List all available languages:

.. code-block:: python

   from xpfcorpus import available_languages

   langs = available_languages()
   print(langs["es"])
   # {"scripts": ["latin"], "default": "latin"}

   print(langs["tt"])
   # {"scripts": ["latin", "cyrillic"], "default": None}

External Data Sources
~~~~~~~~~~~~~~~~~~~~~

Load from external YAML or legacy files:

.. code-block:: python

   from xpfcorpus import Transcriber

   # From YAML file (requires PyYAML)
   custom = Transcriber("custom", yaml_file="my_lang.yaml")

   # From legacy .rules/.verify files
   legacy = Transcriber("test",
                       rules_file="es.rules",
                       verify_file="es.verify")

Command-Line Interface
----------------------

Transcribe Words
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Transcribe words from command line
   xpfcorpus transcribe es ejemplo hola mundo

   # From a file (extracts first word from each line)
   xpfcorpus transcribe es -f words.txt

   # From stdin
   echo -e "mundo\nbueno" | xpfcorpus transcribe es
   cat words.txt | xpfcorpus transcribe es -f -

   # Combine command-line words and file
   xpfcorpus transcribe es ejemplo hola -f more_words.txt

   # JSON output
   xpfcorpus transcribe es ejemplo --json

List Languages
~~~~~~~~~~~~~~

.. code-block:: bash

   # List all available languages
   xpfcorpus list

   # JSON format
   xpfcorpus list --json

Export Language Data
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Export language rules as YAML
   xpfcorpus export es

   # Save to file
   xpfcorpus export es -o spanish.yaml

Verify Language Rules
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Verify a single language
   xpfcorpus verify es

   # Verify with details
   xpfcorpus verify es -v

   # Verify all languages
   xpfcorpus verify --all

Supported Languages
-------------------

The package includes 201 languages with 203 language/script combinations.

Languages with multiple scripts:

* **iu** (Inuktitut): latin, syllabics
* **tt** (Tatar): latin, cyrillic

Use ``xpfcorpus list`` or ``available_languages()`` for the full list.

Citation
--------

If you use this package in your research, please cite the XPF Corpus:

.. code-block:: bibtex

   @misc{xpf_corpus,
     title={The Cross-linguistic Phonological Frequencies (XPF) Corpus},
     author={Cohen Priva, Uriel and Gleason, Emily},
     year={2022},
     url={https://cohenpr-xpf.github.io/XPF/}
   }
