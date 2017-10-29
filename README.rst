jack-matchmaker
===============

Auto-connect JACK ports as they appear and when they match the port patterns
given on the command line or read from a file.


Description
-----------

``jack-matchmaker`` is a small command line utility that listens to JACK port
registrations by clients and connects them when they match one of the port
pattern pairs given on the command line at startup. ``jack-matchmaker`` never
disconnects any ports.

The port name patterns are specified as pairs of positional arguments or read
from a file (see below) and are interpreted as `Python regular expressions`_,
where the first pattern of a pair is matched against output (readable) ports
and the second pattern of a pair is matched against input (writable) ports.
Matching is done against the normal port names as well as any aliases they have
(run "``jack-matchmaker -oia``" to list all available ports with their aliases).

As many pattern pairs as needed can be given.


Installation
------------

Before you install the software, please refer to the section "Requirements".

Then simply do::

    pip install jack-matchmaker

There is also an `AUR package`_ available for Arch Linux users.


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


Pattern files
-------------

In addition to or instead of from positional arguments on the command line,
port patterns can also be read from a file given with the ``-p/--pattern-file``
option. The file must list one port pattern per line, where the first line of
every pair of two lines specifies the output port pattern, and the second
specifies the input port pattern. Empty lines and lines starting with a
hash-sign (``#``) are ignored and whitespace at the start or the end of each
line is stripped.

Example file::

    # left channel
    .*:out_l
        system:playback_1

    # right channel
    .*:out_r
        system:playback_2

When you send a HUP signal to a running ``jack-matchmaker`` process, the file
that was specified on the command line when the process was started is re-read
and the resulting patterns replace *all* previously used patterns. If there is
an error reading the file, the pattern list will then be empty.


JACK server connection
----------------------

``jack-matchmaker`` needs a connection to a running JACK server to be notified
about new ports. On start-up it tries to connect to JACK until a connection can
be established or the maximum number of connection attempts is exceeded. This
number can be set with the command line option ``-m/--max-attempts``, which
defaults to ``0`` (i.e. infinite attempts or until interrupted).
``jack-matchmaker`` waits for 3 seconds between each connection attempt by
default. Change this interval with the option ``-I/--connect-interval``.

When ``jack-matchmaker`` is connected and the JACK server is stopped, the
shutdown event is signalled to ``jack-matchmaker``, which then enters the
connection loop described above again.

To disconnect from the JACK server and stop ``jack-matchmaker``, press
Control-C.


Requirements
------------

* A version of Python 3 with a ``ctypes`` module (i.e. PyPy 3 works too).
* JACK_ version 1 or 2.
* Linux, OS X (untested) or Windows (untested, no signal handling).


License
-------

``jack-matchmaker`` is licensed under the GNU Public License Version v2.

Please see the file ``LICENSE`` for more information.


Acknowledgements
----------------

``jack-matchmaker`` is written in Python and incorporates the ``jacklib``
module taken from falkTX's Cadence_ application.

It was inspired by jack-autoconnect_, which also auto-connects JACK ports, but
doesn't support port aliases. jack-autoconnect is also written in C++, and
therefore probably faster and less memory hungry.

The idea to read ports (patterns) from a file and re-read them on the HUP
signal was "inspired" by aj-snapshot_.

There is also a similar tool called jack-plumbing_, part of the jack-tools_
package on popular Linux distributions.


.. _cadence: https://github.com/falkTX/Cadence/blob/master/src/jacklib.py
.. _jack: http://jackaudio.org/
.. _jack-autoconnect: https://github.com/kripton/jack_autoconnect
.. _python regular expressions: https://docs.python.org/3/library/re.html#regular-expression-syntax
.. _aj-snapshot: http://aj-snapshot.sourceforge.net/
.. _AUR package: https://aur.archlinux.org/packages/jack-matchmaker/
.. _jack-plumbing: http://rd.slavepianos.org/sw/rju/md/jack-plumbing.md
.. _jack-tools: https://packages.ubuntu.com/search?keywords=jack-tools&searchon=names&suite=all&section=all
