jack-matchmaker
===============

Auto-connect new JACK ports matching the patterns given on the command line.

Description
-----------

A small command line utility that reacts to JACK port registrations by clients and connects them
when they match one of the port pattern pairs given on the command line at startup.

The port name patterns are specified as positional arguments and are interpreted as regular
expressions, where the first pattern of a pair is matched against output (readable) ports and the
second pattern of a pair is matched against input (writable) ports. Matching is done against the
normal port names as well as any aliases they may have (you can use `jack_lsp -A` to list all
available ports with their aliases).

As many pattern pairs as needed can be given.


Usage
-----

Automatically connect the first two ports of Fluidsynth to the audio outs::

    jack-matchmaker "fluidsynth:l_01" "system:playback_1" \
                    "fluidsynth:r_01" "system:playback_2"


Acknowledgements
----------------

`jack-matchmaker` is written in Python and incorporates the `jacklib` module taken from falkTX's
Cadence_ application.

It was inspired by jack-autoconnect_, which basically does the same thing, but doesn't
support port aliases. It's also written in C++, and therefore probably much faster and and less
memory hungry. 

.. _cadence: https://github.com/falkTX/Cadence/blob/master/src/jacklib.py
.. _jack-autoconnect: https://github.com/kripton/jack_autoconnect
