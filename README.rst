jack-matchmaker
===============

Auto-connect JACK ports as they appear and match the patterns given on the
command line.


Description
-----------

A small command line utility that reacts to JACK port registrations by clients
and connects them when they match one of the port pattern pairs given on the
command line at startup.

The port name patterns are specified as pairs of positional arguments and are
interpreted as `Python regular expressions`_, where the first pattern of a pair
is matched against output (readable) ports and the second pattern of a pair is
matched against input (writable) ports. Matching is done against the normal
port names as well as any aliases they have (run "``jack-matchmaker -la``" to
list all available ports with their aliases).

As many pattern pairs as needed can be given.


Usage
-----

Automatically connect the first two ports of Fluidsynth to the audio outs::

    jack-matchmaker "fluidsynth:l_01" "system:playback_1" \
                    "fluidsynth:r_01" "system:playback_2"

Both the output port and the input port patterns can be regular expressions.
If a match is found on an output port, the matching port will be connected to
all input ports, which match the corresponding input port pattern::

    jack-matchmaker "fluidsynth:l_\d+" "system:playback_[13]" \
                    "fluidsynth:r_\d+" "system:playback_[24]"

You can also use named regular expression groups in the output port pattern and
fill the strings they match to into placeholders in the input port pattern::

    jack-matchmaker "system:midi_capture_(?P<num>\d+)" \
                    "mydaw:midi_in_track_{num}"

Run ``jack-matchmaker -h`` (or ``--help``) to show help on the available
command line options.


Requirements
------------

* A version of Python 3 with a `ctypes` module (i.e. PyPy 3 works too) .
* JACK_ version 1 or 2.
* Linux, OS X (untested) or Windows (untested).


Acknowledgements
----------------

`jack-matchmaker` is written in Python and incorporates the `jacklib` module
taken from falkTX's Cadence_ application.

It was inspired by jack-autoconnect_, which also auto-connects JACK ports, but
doesn't support port aliases. jack-autoconnect also written in C++, and
therefore probably faster and less memory hungry.


.. _cadence: https://github.com/falkTX/Cadence/blob/master/src/jacklib.py
.. _jack: http://jackaudio.org/
.. _jack-autoconnect: https://github.com/kripton/jack_autoconnect
.. _python regular expressions: https://docs.python.org/3/library/re.html#regular-expression-syntax
