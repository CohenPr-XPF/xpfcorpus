Command-Line Interface
======================

The ``xpfcorpus`` command provides a comprehensive CLI for transcription and language management.

Commands
--------

transcribe
~~~~~~~~~~

Transcribe words from graphemes to phonemes.

.. code-block:: bash

   xpfcorpus transcribe LANGUAGE [WORDS...] [OPTIONS]

**Arguments:**

* ``LANGUAGE`` - Language code (e.g., "es", "tt"). Supports BCP-47 style codes with script/region (e.g., "es-ES", "yi-Latn", "tt-cyrillic")
* ``WORDS`` - Words to transcribe (optional if using ``-f``)

**Options:**

* ``-s, --script SCRIPT`` - Script to use (e.g., "latin", "cyrillic")
* ``-f, --file FILE`` - Read words from FILE (use "-" for stdin). Extracts first word from each line.
* ``--yaml FILE`` - Use external YAML file
* ``--rules FILE`` - Use legacy .rules file
* ``--verify-file FILE`` - Use legacy .verify file
* ``--no-verify`` - Skip verification on load
* ``--json`` - Output as JSON

**Examples:**

.. code-block:: bash

   # Transcribe command-line arguments
   xpfcorpus transcribe es ejemplo hola mundo

   # From a file
   xpfcorpus transcribe es -f words.txt

   # From stdin
   echo -e "mundo\nbueno" | xpfcorpus transcribe es
   cat words.txt | xpfcorpus transcribe es -f -

   # Combine sources
   xpfcorpus transcribe es ejemplo -f more_words.txt

   # With BCP-47 codes
   xpfcorpus transcribe es-ES ejemplo
   xpfcorpus transcribe yi-Latn shalom
   xpfcorpus transcribe tt-cyrillic привет

   # JSON output
   xpfcorpus transcribe es ejemplo --json

   # Explicit script
   xpfcorpus transcribe tt -s cyrillic привет

list
~~~~

List all available languages.

.. code-block:: bash

   xpfcorpus list [OPTIONS]

**Options:**

* ``--json`` - Output as JSON

**Examples:**

.. code-block:: bash

   # Human-readable list
   xpfcorpus list

   # JSON format
   xpfcorpus list --json

**Output Format:**

.. code-block:: text

   Available languages: 201

     es: latin (default: latin)
     tt: latin, cyrillic
     yi: hebrew (default: hebrew)
     ...

export
~~~~~~

Export a language's rules as YAML.

.. code-block:: bash

   xpfcorpus export LANGUAGE [OPTIONS]

**Arguments:**

* ``LANGUAGE`` - Language code to export

**Options:**

* ``-o, --output FILE`` - Output file (default: stdout)

**Examples:**

.. code-block:: bash

   # To stdout
   xpfcorpus export es

   # To file
   xpfcorpus export es -o spanish.yaml

verify
~~~~~~

Verify language rules against test data.

.. code-block:: bash

   xpfcorpus verify [LANGUAGE] [OPTIONS]

**Arguments:**

* ``LANGUAGE`` - Language code to verify (required unless using ``--all``)

**Options:**

* ``-s, --script SCRIPT`` - Script to verify (for multi-script languages)
* ``--all`` - Verify all languages (all scripts for multi-script languages)
* ``-v, --verbose`` - Show error details
* ``-q, --quiet`` - Only show summary
* ``--json`` - Output as JSON

**Examples:**

.. code-block:: bash

   # Verify single language
   xpfcorpus verify es

   # With details
   xpfcorpus verify es -v

   # Specific script
   xpfcorpus verify tt -s cyrillic

   # All languages
   xpfcorpus verify --all

   # Quiet mode (just pass/fail count)
   xpfcorpus verify --all -q

   # JSON output
   xpfcorpus verify --all --json

**Output Format:**

.. code-block:: text

   aak: PASS
   ab: PASS
   acf: PASS
   ...
   tt-cyrillic: PASS
   tt-latin: PASS
   ...

   Results: 203/203 passed

Input File Format
-----------------

When using the ``-f`` option with the ``transcribe`` command, the input file should have one word per line. The first word on each line is extracted (splitting on whitespace or commas).

.. code-block:: text

   # words.txt
   ejemplo
   hola, mundo
   buenos días

   # Comments are ignored

Lines starting with ``#`` are treated as comments and ignored.

Exit Codes
----------

* ``0`` - Success
* ``1`` - Error (language not found, verification failed, etc.)
* ``127`` - Command not found (package not installed)
