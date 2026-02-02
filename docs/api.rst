API Reference
=============

Main API
--------

Transcriber
~~~~~~~~~~~

.. autoclass:: xpfcorpus.Transcriber
   :members:
   :special-members: __init__, __repr__
   :exclude-members: __weakref__

available_languages
~~~~~~~~~~~~~~~~~~~

.. autofunction:: xpfcorpus.available_languages

Exceptions
----------

.. automodule:: xpfcorpus.exceptions
   :members:
   :show-inheritance:

Engine Layer
------------

TranscriptionProcessor
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: xpfcorpus.engine.processor.TranscriptionProcessor
   :members:
   :special-members: __init__
   :exclude-members: __weakref__

Data Classes
~~~~~~~~~~~~

.. autoclass:: xpfcorpus.engine.rules.RuleSet
   :members:
   :exclude-members: __weakref__

.. autoclass:: xpfcorpus.engine.rules.SubRule
   :members:
   :exclude-members: __weakref__

.. autoclass:: xpfcorpus.engine.rules.LanguageData
   :members:
   :exclude-members: __weakref__

.. autoclass:: xpfcorpus.engine.rules.ScriptData
   :members:
   :exclude-members: __weakref__

.. autoclass:: xpfcorpus.engine.rules.VerifyEntry
   :members:
   :exclude-members: __weakref__

I/O Layer
---------

PackageRepository
~~~~~~~~~~~~~~~~~

.. autoclass:: xpfcorpus.io.repository.PackageRepository
   :members:

Loaders
~~~~~~~

.. autoclass:: xpfcorpus.io.json_loader.JSONLoader
   :members:

.. autoclass:: xpfcorpus.io.yaml_loader.YAMLLoader
   :members:

.. autoclass:: xpfcorpus.io.legacy_loader.LegacyLoader
   :members:

Language Code Parsing
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: xpfcorpus.io.language_code
   :members:
