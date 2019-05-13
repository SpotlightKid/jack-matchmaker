Changelog
=========

For details and minor changes, please see the `version control log messages
<https://github.com/SpotlightKid/jack-matchmaker/commits/master>`_.


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
