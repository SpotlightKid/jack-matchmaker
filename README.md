# jack-matchmaker

Auto-connect [JACK] ports as they appear and when they match the port patterns
given on the command line or read from a file.

[![Latest version](https://shields.io/pypi/v/jack-matchmaker)](https://pypi.org/project/jack-matchmaker)
[![Date of latest release](https://shields.io/github/release-date/SpotlightKid/jack-matchmaker)](https://github.com/SpotlightKid/jack-matchmaker/releases)
![Project status](https://shields.io/pypi/status/jack-matchmaker)
[![GNU General Public License 2](https://shields.io/pypi/l/jack-matchmaker)](./LICENSE)
![Python versions](https://shields.io/pypi/pyversions/jack-matchmaker)
[![Distribution format](https://shields.io/pypi/format/jack-matchmaker)](https://pypi.org/project/jack-matchmaker/#files)


## Description

`jack-matchmaker` is a small command line utility that listens to port
registrations by JACK clients and connects these ports when their names match
one of the port pattern pairs given on the command line at startup.
`jack-matchmaker` **never disconnects any ports.**

The port name patterns are specified as pairs of positional arguments or read
from a file (see below) and *by default* are always interpreted as
[Python regular expressions], where the first pattern of a pair is matched
against both output (readable) ports and input (writeable) ports, and the
second pattern of a pair is matched only against input ports. As many pattern
pairs as needed can be given.

If the first pattern matches an input port, all output ports connected to that
input port will be connected to the input ports matching the second pattern.

Patterns are matched against:

- normal port names
- port aliases
- [pretty-names]
  set in the port meta data

You can run `jack-matchmaker -oian` to list all available output and input
ports with their aliases and pretty-names.


## Installation

Before you install the software, please refer to the section
"Requirements".

Then simply do:

```con
$ pip install jack-matchmaker
```

There is also an [AUR package] available for Arch Linux users.


## Usage

Run `jack-matchmaker -h` (or `--help`) to show help on the available command
line options.

See also the section "Systemd service" below on how to use `jack-matchmaker` as
a systemd user service.

### Examples

Automatically connect the first two ports of Fluidsynth to the audio outs using
*exact matching* mode:

```con
$ jack-matchmaker -e \
    fluidsynth:l_01 system:playback_1 \
    fluidsynth:r_01 system:playback_2
```

Both the output port and the input port patterns can be regular expressions. If
a match is found on an output port, the matching port will be connected to
*all* input ports, which match the corresponding input port pattern:

```con
$ jack-matchmaker \
    'fluidsynth:l_\d+' 'system:playback_[13]' \
    'fluidsynth:r_\d+' 'system:playback_[24]'
```

You can also use named regular expression groups in the output port pattern and
fill the port name sub-strings they match to into placeholders in the input
port pattern:

```con
$ jack-matchmaker \
    'system:midi_capture_(?P<num>\d+)$' 'mydaw:midi_in_track_{num}'
```

Automatically connect all ports going to the system output to an FFmpeg
recording instance as well:

```con
$ jack-matchmaker \
    'system:playback_(?P<num>\d+)$' 'ffmpeg:input_{num}'
```


### Regular expression and exact matching

By default port name patterns are always interpreted as
[Python regular expressions] and are matched against port names, aliases and
pretty-names using case-sensitive matching. They are anchored to the start of
the string they match, i.e. they must match the start of the port name, but
they still match, if the port name continues after the part the pattern matches.

E.g. the pattern `client:out_\d` matches `client:out_1`, `client:out_2` etc.
and also `client:out_10` (even though the trailing zero is not included in the
pattern), but does not match `otherclient:out_1`.

You can still match port names with arbitrary prefixes by using `.*` at the
start of the pattern, e.g. `.*client:out_\d`.

To anchor the pattern to the end of the matched string as well, use a `$` at
the end of the pattern. E.g `client:out_[12]$` will match `client:out_1` and
`client:out_2`, but not `client:out_10`, `client:out_21` etc.

To use exact string matching instead of regular expression matching, use the
`-e`, `--exact-matching` command line option. When this option is given,
patterns must match port names (or aliases or pretty-names) exactly. You can
still use regular expression patterns by enclosing a pattern in forward
slashes, e.g. like so:

```con
$ jack-matchmaker -e system:capture_1 '/myclient:in_l_\d+/'
```

All this applies to patterns given as positional command line arguments *and*
to patterns listed in a pattern file (see below).


### Pattern match group substitution

An output port pattern can contain one or more *named groups* with the syntax
`(?P<name>...)`, where the three dots represent a sub regular expression. The
part of the port name matched by this sub regex, is available as a substitution
value for a placeholder corresponding to the name of group in the input port
pattern. Placeholders use the [Python string formatting] syntax.

Example:

```con
$ jack-matchmaker \
    'mysynth:out_(?P<channel>[lr])_\d+$' 'myfx:in_{channel}$'
```

This would connect all ports named `mysynth:out_l_1`, `mysynth:out_l_2` and so
on to `myfx:in_l` and all ports named `mysynth:out_r_1`, `mysynth:out_r_2` and
so on to `myfx:in_r`.

### Pattern files

In addition to or instead of listing port patterns as as positional arguments
on the command line, port patterns can also be put in a textfile.

The `-p`, `--pattern-file` option instructs the program to read the patterns
from the file path given as the option value. The file must list one port
pattern per line, where the first line of every pair of two lines specifies the
output port pattern, and the second specifies the input port pattern. Empty
lines and lines starting with a hash-sign (`#`) are ignored and whitespace at
the start of the end of each line is stripped.

Example file:

```
# Left channel
# This will match output ports of any client named
# 'out_1', 'out_l', 'output_1' or 'output_l'
.*:out(put)?_(1|l)$
    system:playback_1

# Right channel
# This will match output ports of any client named
# 'out_2', 'out_r', 'output_2' or 'output_r'
.*:out(put)?_(2|r)$
    system:playback_2

# Another common naming scheme for output ports:
.*:Out L
    system:playback_1

.*:Out R
    system:playback_2
```


#### Easy pattern file creation

Set up your JACK connections using GUI tools like `QJackCtl` or `Carla` first.
Then use `jack-matchmaker -c > patterns` to save a the current JACK connections
in the file `patterns` in a *pattern file compatible* format. You may then edit
this file and and delete or add pattern pairs as needed.

When using the `-c` option, you can also optionally give one or more regular
expression patterns as positional arguments on the command line. In that case
only connections, where any of the given patterns is matching (part of) either
the output or input port names, are listed. If the patterns contain any
uppercase letters, they will be matched in a case-sensitive fashion, if not,
they will be matched case-insensitively. The patterns are matched against the
full port name, including the client name. For example:

```con
$ jack-matchmaker -c JACK
```

This would list connections, where one of the connected ports contains "JACK"
in its name, but not if it contained only "jack" or "Jack" (unless matched by
another pattern).


#### Reloading the pattern file

When you send a HUP signal to a running `jack-matchmaker` process, the file
that was specified on the command line when the process was started is re-read
and the resulting patterns replace *all* previously used patterns (including
those listed as positional command line arguments!). If there should be an
error reading the file, the pattern list will then be empty.

On systemd you can use `systemctl --user reload jack-matchmaker` to reload the
pattern file.


## JACK server connection

`jack-matchmaker` needs a connection to a running JACK server to be notified
about new ports. On start-up it tries to connect to JACK until a connection can
be established or the maximum number of connection attempts is exceeded. This
number can be set with the command line option `-m`, `--max-attempts`, which
defaults to `0` (i.e. infinite attempts or until interrupted).
`jack-matchmaker` waits for 3 seconds between each connection attempt by
default. Change this interval with the option `-I`, `--connect-interval`.

When `jack-matchmaker` is connected and the JACK server is stopped, the
shutdown event is signaled to `jack-matchmaker`, which then enters the
connection loop described above again.

To disconnect from the JACK server and stop `jack-matchmaker`, send an INT
signal to the process, usually done by pressing Control-C in the terminal where
`jack-matchmaker` is running.


## Systemd service

You can optionally install `jack-matchmaker` as a systemd user service:

```con
$ install -Dm644 systemd/jack-matchmaker.conf /etc/conf.d/jack-matchmaker
$ install -Dm644 systemd/jack-matchmaker.service -t /usr/lib/systemd/user
```

To start the service, edit `/etc/conf.d/jack-matchmaker` according to your
needs (see section "Environment file" below) and then start the service with:

```con
$ systemctl --user start jack-matchmaker
```

To stop it again:

```con
$ systemctl --user stop jack-matchmaker
```

To reload the pattern file:

```con
$ systemctl --user reload jack-matchmaker
```


### Environment file

The `jack-matchmaker` systemd user service reads an environment file, which is
expected to be located at `/etc/conf.d/jack-matchmaker`. In this file, you can
set the following service startup settings as environment variables:

`PATTERN_FILE` (default: `"/etc/jack-matchmaker/patterns.txt"`)

A file with port pattern pairs to read at startup as described above in section
"Pattern files".

`PATTERNS`

A space-separated list of port patterns in pairs of two. The default list is
empty and it is recommened to use `PATTERN_FILE` instead when running
`jack-matchmaker` as a systemd service, unless the patterns should remain
static and never change.

`CLIENT_NAME` (default: `"jack-matchmaker"`)

Set the JACK client name used by `jack-matchnmaker` to the given value.

`CONNECT_INTERVAL` (default: `3`)

Set the interval in seconds between attempts to connect to JACK server to the
given numeric value.

`EXACT_MATCHING`

Enable literal matching mode. Patterns must match port names exactly. To still
use regular expressions, surround a port pattern with forward slashes, e.g.
`"/system:out_\d+/"`.

Set `EXACT_MATCHING` to any value to enable it.

`MAX_ATTEMPTS` (default: `0`)

Set the maximum number of attempts to connect to JACK server before giving up.
The default value `0` means to keep on trying until interrupted.

`VERBOSITY` (default: `INFO`)

Set output verbosity level. Choices are: `DEBUG`, `INFO`, `WARNING`, and
`ERROR`.


## Requirements

- A version of Python 3 with a `ctypes` module (i.e. PyPy 3 works too)
- [pyjacklib]
- [cachetools]
- [JACK] version 1 or 2
- Linux, OS X (untested) or Windows (untested, no signal handling)


## License

`jack-matchmaker` is licensed under the GNU Public License Version v2.

Please see the file `LICENSE` for more information.

## Author

`jack-matchmaker` was written by Christopher Arndt 2016 - 2023.


## Acknowledgements

`jack-matchmaker` is written in Python and depends on the [pyjacklib] module,
which was originally taken from falkTX's [Cadence] application but now turned
into a stand-alone Python package and was heavily modified and extended in
the process.

It was inspired by [jack-autoconnect], which also auto-connects JACK ports, but
doesn't support port aliases or meta data pretty-names. jack-autoconnect is
also written in C++, and therefore probably faster and less memory hungry.

The idea to read ports (patterns) from a file and re-read them on the HUP
signal was "inspired" by [aj-snapshot].

There is also a similar tool called `jack-plumbing`, part of the [jack-tools]
package on popular Linux distributions.


[AUR package]: https://aur.archlinux.org/packages/jack-matchmaker/
[Cadence]: https://github.com/falkTX/Cadence/blob/master/src/jacklib.py
[aj-snapshot]: https://aj-snapshot.sourceforge.net/
[cachetools]: https://github.com/tkem/cachetools/
[jack-autoconnect]: https://github.com/kripton/jack_autoconnect
[JACK]: http://jackaudio.org/
[jack-tools]: https://packages.ubuntu.com/search?keywords=jack-tools&searchon=names&suite=all&section=all
[pretty-names]: https://github.com/jackaudio/jackaudio.github.com/wiki/JACK-Metadata-API
[pyjacklib]: https://github.com/jackaudio/pyjacklib
[Python regular expressions]: https://docs.python.org/3/library/re.html#regular-expression-syntax
[Python string formatting]: https://docs.python.org/3/library/string.html#formatstrings
