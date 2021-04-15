Changelog
=========

For details and minor changes, please see the `version control log messages
<https://github.com/SpotlightKid/jack-matchmaker/commits/master>`_.


2021-04-15 version 0.10.0
-------------------------

Enhancement:

* Added support for filtering against port name patterns when listing
  connections with option ``-c```.


2021-01-15 version 0.9.0
------------------------

Changes:

* Dropped official support for Python 3.5 and declared support for Python 3.9.
  Incremented the minor version accordingly.

Enhancement:

* Added support for the ``reload`` action to the jack-matchmaker systemd
  service, which triggers re-reading of the pattern file (thanks to BlueMax).


2020-08-05 version 0.8.2
------------------------

Changes:

* Max. connection attempt is always set to 1 when any of the ``-c``, ``-i`` or
  ``-o`` options are used.

Enhancement:

* Log JACK client name after connection (if verbosity is ``DEBUG``).
* Only log connection error traceback when verbosity is ``DEBUG``.
* Improve warning logging of non-fatal connection error status.

Fixes:

* Correctly check for valid JACK client when connecting (thanks to Filipe
  Coelho for reporting).


2020-08-05 version 0.8.1
------------------------

Fixes:

* Fixed not connecting to JACK when an instance of jack-matchmaker was already
  running and no unique JACK client name set (#11, thanks to Nils Hilbricht for
  reporting).


2020-01-19 version 0.8.0
------------------------

Changes:

* Removed Python 3.4 support, added 3.8.

Enhancements:

* Added optional systemd unit along with environment file (thanks to
  Térence Clastres).
* Added Arch Linux ``PKGBUILD`` file.
* Added ``--verbosity`` command line option for setting a
  specific log level (thanks to Térence Clastres).

Fixes:

* Added graceful handling of ``Ctrl-C`` when connecting.
* Added handling of error reading pattern file on startup.
* Changed ``__main__.py`` to import from the package it is in.
* Fixed wrong argument name of ``jacklib.remove_client_property``.


2019-05-13 version 0.7.1
------------------------

Fixes:

* Fix incompatibility with Python < 3.7, due to use of ``re.Pattern`` and
  ``re.Match``, which were only added in Python 3.7.

  Python 3.4 is still supported, but will be dropped in next major release.


2019-04-15 version 0.7.0
------------------------

New features:

* Added support for listing and matching port `meta data`_ pretty-names
  (supported only with JACK1 or JACK2 >= 1.9.13 or development version).
* Added command line option ``-e``, ``--exact-matching`` for exact port name
  matching mode.
* Added command line option ``-N``, ``--client-name`` to set JACK client name.

Enhancements:

* Expanded documentation in README_ to explain pattern matching and
  match group substitution and with more and better examples.
* Added badge images & links to README_.
* Improved handling of port name decoding.
* Added a couple of example scripts for ``jacklib`` usage to repo.
* Updated Python versions in ``setup.py`` classifiers.

Fixes:

* Re-compile input port pattern for each output port as it may have changed
  due to match group substitution.
* Fixed probable memory leak from not freeing ``jack_get_ports`` results.
* Fixed wrong return type of JACK port rename callback function declaration.
* Removed unused ``alsainfo`` module.


2017-10-17 version 0.6.0
------------------------

* Automatically tries to re-connect to JACK if the server not available on
  start-up or shuts down while ``jack-matchmaker`` is running.
* Added sections to README_ on installation, license and jack server
  connection.


2016-11-05 version 0.5.0
------------------------

* Reorganized command line options: ``-l``, ``--list-ports`` was replaced by
  ``-o``/``--list-outputs`` and ``-i``, ``--list-inputs``, which can be given
  on their own or together and in combination with the ``-a``,
  ``--list-aliases`` option.
* Removed prefixes and separators from port and connection listings (so the
  output can be more easily parsed in shell scripts or the output of
  ``jack-matchmaker -c`` can be piped into a file and directly used with the
  ``-p``, ``--pattern-file`` option).
* Added ``--version`` command line option.
* Excluded currently unused ``alsainfo`` module from distribution.
* Re-formatted some code for PEP-8 conformity.


2016-11-04 version 0.4.0
------------------------

* Added support for -c command line option to list existing JACK port
  connections.


2016-11-04 version 0.3.0
------------------------

* Added command line option to read port patterns from file.
* Re-read pattern file on HUP signal (not supported on Windows).
* Check if ports are already connected before making a connection.
* Cache port look-ups.
* List outputs before inputs.
* Changed amount and formatting of debug logging output.
* Added example patterns file.
* Updated README_ with new features.


2016-11-04 version 0.2.1
------------------------

* Fixed missing exception variable binding.
* Moved package version from ``setup.py`` to new ``version`` module.
* Minor README_ improvements.


2016-11-04 version 0.2.0
------------------------

* Added command line options to list ports and aliases.
* Input port patters can contain placeholders which are filled in with matches
  from named regular expression groups in output port patterns.
* Call on-connection callback once at startup to connect existing clients.
* Updated and improve README_.
* Improved error handling.


2016-11-04 version 0.1.0
------------------------

First public release.


.. _readme: README.rst
.. _meta data: https://github.com/jackaudio/jackaudio.github.com/wiki/JACK-Metadata-API
