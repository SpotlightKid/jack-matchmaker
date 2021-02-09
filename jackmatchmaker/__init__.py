# -*- coding: utf-8 -*-
"""Auto-connect new JACK ports matching the patterns given on the command line."""

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import logging
import re
import signal
import sys
import time

from collections import defaultdict
from functools import lru_cache
from itertools import chain

try:
    import queue
except ImportError:
    import Queue as queue

from . import jacklib
from .jacklib_helpers import c_char_p_p_to_list, get_jack_status_error_string
from .version import __version__


__program__ = "jack-matchmaker"
PROPERTY_CHANGE_MAP = {
    jacklib.PropertyCreated: 'created',
    jacklib.PropertyChanged: 'changed',
    jacklib.PropertyDeleted: 'deleted'
}
log = logging.getLogger(__program__)

if not hasattr(re, 'Pattern'):
    re.Pattern = re._pattern_type

if not hasattr(re, 'Match'):
    re.Match = type(re.match('', ''))


def pairwise(iterable):
    """s -> (s0,s1), (s2,s3), (s4, s5), ..."""
    args = [iter(iterable)] * 2
    return zip(*args)


def flatten(nestedlist):
    """Flatten one level of nesting."""
    return chain.from_iterable(nestedlist)


def posnum(arg):
    """Make sure that command line arg is a positive number."""
    value = float(arg)
    if value < 0:
        raise argparse.ArgumentTypeError("Value must not be negative!")
    return value


class JackMatchmaker(object):
    def __init__(self, patterns, pattern_file=None, name=__program__, exact_matching=False,
                 connect_interval=3.0, connect_max_attempts=0):
        self.patterns = []
        self.pattern_file = pattern_file
        self.client_name = name
        self.exact_matching = exact_matching
        self.connect_max_attempts = connect_max_attempts
        self.connect_interval = connect_interval
        self.default_encoding = jacklib.ENCODING

        jacklib.set_error_function(self.error_callback)

        if self.pattern_file:
            try:
                self.add_patterns_from_file(self.pattern_file)
            except OSError:
                log.error("Could not read pattern file '%s'.", self.pattern_file)
                raise

            if not sys.platform.startswith('win'):
                signal.signal(signal.SIGHUP, self.reread_pattern_file)
            else:
                log.warning("Signal handling not supported on Windows. jack-matchmaker must be "
                            "restarted to re-read the pattern file.")

        for pair in patterns:
            self.add_patterns(*pair)

        self.queue = queue.Queue()
        self.client = None

    def connect(self, max_attempts=None):
        if max_attempts is None:
            max_attempts = self.connect_max_attempts

        tries = 0
        while True:
            log.debug("Attempting to connect to JACK server...")
            status = jacklib.jack_status_t()
            self.client = jacklib.client_open(self.client_name, jacklib.JackNoStartServer, status)
            tries += 1

            if status.value:
                err = get_jack_status_error_string(status)
                if status.value & jacklib.JackNameNotUnique:
                    log.debug(err)
                elif status.value & jacklib.JackServerStarted:
                    # Should not happen, since we use the JackNoStartServer option
                    log.warning("Unexpected JACK status: %s", err)
                else:
                    log.warning("JACK connection error (attempt %i): %s", tries, err)

            if self.client:
                break

            if max_attempts and tries >= max_attempts:
                log.error("Maximum number (%i) of connection attempts reached. Aborting.",
                          max_attempts)
                raise RuntimeError(err)

            log.debug("Waiting %.2f seconds to connect again...", self.connect_interval)
            time.sleep(self.connect_interval)

        name = jacklib.get_client_name(self.client)
        if name is not None:
            self.client_name = name.decode()
        else:
            raise RuntimeError("Could not get JACK client name.")

        jacklib.on_shutdown(self.client, self.shutdown_callback, None)
        log.debug("Client connected, name: %s UUID: %s", self.client_name,
                  jacklib.client_get_uuid(self.client))

    def close(self):
        if self.client:
            jacklib.deactivate(self.client)
            return jacklib.client_close(self.client)

    def add_patterns(self, ptn_output, ptn_input):
        if not self.exact_matching or (ptn_output.startswith('/') and ptn_output.endswith('/')):
            try:
                ptn_output = re.compile(ptn_output.strip('/'))
            except re.error as exc:
                log.error("Error in output port pattern '%s': %s", ptn_output, exc)
                return

        if not (ptn_output, ptn_input) in self.patterns:
            pattern = ptn_output.pattern if isinstance(ptn_output, re.Pattern) else ptn_output
            log.debug("Added patterns: '%s' --> '%s'", pattern, ptn_input)
            self.patterns.append((ptn_output, ptn_input))

    def add_patterns_from_file(self, filename):
        with open(filename) as fp:
            stripfilter = (line.strip() for line in fp)
            linefilter = (line for line in stripfilter if line and not line.startswith('#'))

            for ptn_output, ptn_input in pairwise(linefilter):
                self.add_patterns(ptn_output, ptn_input)

    def reread_pattern_file(self, sig_no, frame):
        log.debug("HUP signal received. Re-reading patterns from '%s'.", self.pattern_file)
        self.patterns = []

        try:
            self.add_patterns_from_file(self.pattern_file)
        except OSError as exc:
            log.error("Could not read pattern file '%s': %s", self.pattern_file, exc)
        else:
            self._refresh()

    def property_callback(self, subject, name, type_, *args):
        if name:
            name = name.decode(self.default_encoding, errors='ignore')

        log.debug("Property '%s' on subject %s %s.", name, subject, PROPERTY_CHANGE_MAP[type_])
        self._refresh()

    def rename_callback(self, port_id, old_name, new_name, *args):
        if old_name:
            old_name = old_name.decode(self.default_encoding, errors='ignore')

        if new_name:
            new_name = new_name.decode(self.default_encoding, errors='ignore')

        log.debug("Port name %s changed to %s.", old_name, new_name)
        self._refresh()

    def reg_callback(self, port_id, action, *args):
        if action == 0:
            return

        port = jacklib.port_by_id(self.client, port_id)
        log.debug("New port registered: %s", jacklib.port_name(port))
        self._refresh()

    def error_callback(self, error):
        error = error.decode(self.default_encoding, errors='ignore')
        log.debug(error)

    def _refresh(self):
        inputs = list(flatten(self.get_ports(jacklib.JackPortIsInput)))
        outputs = list(flatten(self.get_ports(jacklib.JackPortIsOutput)))

        for ptn_output, ptn_input in self.patterns:
            for output in outputs:
                if isinstance(output, tuple):
                    real_output, output = output
                else:
                    real_output = None

                if isinstance(ptn_output, re.Pattern):
                    log.debug("Match regex '%s' on output port '%s'.", ptn_output.pattern, output)
                    match_output = ptn_output.match(output)
                else:
                    match_output = ptn_output == output

                if match_output:
                    log.debug("Found matching output port: %s", output)

                    if isinstance(match_output, re.Match):
                        # try to fill-in groups matches from output port
                        # pattern into input port pattern
                        try:
                            subst = defaultdict(str, **match_output.groupdict())
                            ptn_input_xformed = ptn_input.format_map(subst)
                        except Exception as exc:
                            log.warn("Could not merge match groups into input pattern '%s': %s",
                                     ptn_input, exc)
                            ptn_input_xformed = ptn_input
                    else:
                        ptn_input_xformed = ptn_input

                    if not self.exact_matching or (ptn_input_xformed.startswith('/')
                                                   and ptn_input_xformed.endswith('/')):
                        try:
                            ptn_input_xformed = re.compile(ptn_input_xformed.strip('/'))
                        except re.error as exc:
                            log.error("Error in input port pattern '%s': %s",
                                      ptn_input_xformed, exc)
                            continue

                    for input in inputs:
                        if isinstance(input, tuple):
                            real_input, input = input
                        else:
                            real_input = None

                        if isinstance(ptn_input_xformed, re.Pattern):
                            log.debug("Match regex '%s' on input port '%s'.",
                                      ptn_input_xformed.pattern, input)
                            match_input = ptn_input_xformed.match(input)
                        else:
                            match_input = ptn_input_xformed == input

                        if match_input:
                            log.debug("Found matching input port: %s", input)
                            self.queue.put((real_output or output, real_input or input))

    def shutdown_callback(self, *args):
        """
        If JACK server signals shutdown, sent ``None`` to the queue to cause client to reconnect.
        """
        log.debug("JACK server signalled shutdown.")
        self.client = None
        self.queue.put(None)

    @lru_cache()
    def _get_port(self, name):
        return jacklib.port_by_name(self.client, name)

    def _get_aliases(self, port_name):
        port = self._get_port(port_name)
        num_aliases, *aliases = jacklib.port_get_aliases(port)
        return list(aliases[:num_aliases])

    def get_ports(self, type_=jacklib.JackPortIsOutput, include_aliases=True,
                  include_pretty_names=True):
        for port_name in c_char_p_p_to_list(jacklib.get_ports(self.client, '', '', type_)):
            ports = [port_name]

            if include_aliases:
                aliases = self._get_aliases(port_name)
                ports.extend(aliases)

            if include_pretty_names:
                pretty_name = jacklib.get_port_pretty_name(self.client, port_name)

                if pretty_name:
                    try:
                        client, port = port_name.split(':', 1)
                    except ValueError:
                        pass
                    else:
                        pretty_name = client + ':' + pretty_name

                    ports.append((port_name, pretty_name))

            yield ports

    def get_connections(self, ports=None):
        if ports is None:
            ports = (p[0] for p in self.get_ports())

        for port_name in ports:
            port = jacklib.port_by_name(self.client, port_name)

            if jacklib.port_connected(port):
                for other in jacklib.port_get_all_connections(self.client, port):
                    yield((port_name, other))

    def list_connections(self, patterns):
        for outport, inport in self.get_connections():
            if patterns:
                match = False
                for ptn in patterns:
                    flags = re.I if ptn.lower() == ptn else 0

                    if re.search(ptn, outport, flags) or re.search(ptn, inport, flags):
                        match = True
                        break
            else:
                match = True

            if match:
                print("%s\n    %s\n" % (outport, inport))

    def list_ports(self, type_=jacklib.JackPortIsOutput, include_aliases=True,
                   include_pretty_names=True):
        print(self._format_ports(self.get_ports(type_, include_aliases, include_pretty_names)),
              end='\n\n')

    def _format_ports(self, ports):
        out = []
        for output in ports:
            out.append(output[0])

            for alias in output[1:]:
                if isinstance(alias, tuple):
                    alias = alias[1]
                out.append("    %s" % alias)

        return "\n".join(out)

    def run(self):
        while True:
            try:
                self.connect()
                jacklib.set_port_registration_callback(self.client, self.reg_callback, None)
                jacklib.set_port_rename_callback(self.client, self.rename_callback, None)
                jacklib.set_property_change_callback(self.client, self.property_callback, None)
                jacklib.activate(self.client)
                # Set up connections for existing clients/ports.
                self._refresh()

                while True:
                    try:
                        event = self.queue.get(timeout=1)
                    except queue.Empty:
                        pass
                    else:
                        if event is None:
                            break
                        else:
                            outport, inport = event

                        if not jacklib.port_connected_to(self._get_port(outport), inport):
                            log.info("Connecting ports '%s' --> '%s'.", outport, inport)
                            jacklib.connect(self.client, outport, inport)
                        else:
                            log.debug("Ports '%s' and '%s' already connected.", outport, inport)
            except KeyboardInterrupt:
                return


def main(args=None):
    ap = argparse.ArgumentParser(prog=__program__, description=__doc__.splitlines()[0])
    apg = ap.add_argument_group('actions', 'Listing ports and connections')
    apg.add_argument('-c', '--list-connections', dest="actions", action="append_const",
                     const="list_cnx", help="List all connections between JACK ports "
                     "(optionally with pattern matching)")
    apg.add_argument('-i', '--list-inputs', dest="actions", action="append_const",
                     const="list_ins", help="List all JACK input ports")
    apg.add_argument('-o', '--list-outputs', dest="actions", action="append_const",
                     const="list_outs", help="List all JACK output ports")
    apg.add_argument('-a', '--aliases', action="store_true",
                     help="Include aliases when listing ports")
    apg.add_argument('-n', '--pretty-names', action="store_true",
                     help="Include pretty-names from port meta data when listing ports")
    ap.add_argument('-p', '--pattern-file', metavar="FILE",
                    help="Read pattern pairs from FILE (one pattern per line)")
    ap.add_argument('-e', '--exact-matching', action="store_true",
                    help="Enable literal matching mode. Patterns must match port names exactly. "
                         "To still use regular expressions, mark them with slashes, e.g. "
                         "'/system:out_\\d+/'.")
    ap.add_argument('-N', '--client-name', metavar='NAME', default=__program__,
                    help="Set JACK client name to NAME (default: '%(default)s')")
    ap.add_argument('-I', '--connect-interval', type=posnum, default=3.0, metavar="SECONDS",
                    help="Interval between attempts to connect to JACK server "
                    " (default: %(default)s)")
    ap.add_argument('-m', '--max-attempts', type=posnum, default=0, metavar="NUM",
                    help="Max. number of attempts to connect to JACK server (default: 0=infinite)."
                          " Always 1 when any of the -c, -i or -o options are used.")
    ap.add_argument('-v', '--verbosity', nargs='?', metavar="LEVEL",
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], const='DEBUG', default='INFO',
                    help="Set verbosity level (choices: %(choices)s, default: %(default)s). "
                         "Passing no arguments sets it to DEBUG.")
    ap.add_argument('--version', action='version', version='%%(prog)s %s' % __version__)
    ap.add_argument('patterns', nargs='*', help="Port pattern (pairs)")
    args = ap.parse_args(args)

    logging.basicConfig(level=args.verbosity, format="%(levelname)s: %(message)s")

    if args.patterns and args.pattern_file:
        log.warning("Port pattern pairs from command line will be discarded when pattern file is "
                    "re-read on HUP signal.")

    if args.actions or args.patterns or args.pattern_file:
        try:
            matchmaker = JackMatchmaker(pairwise(args.patterns), args.pattern_file,
                                        name=args.client_name, exact_matching=args.exact_matching,
                                        connect_interval=args.connect_interval,
                                        connect_max_attempts=args.max_attempts)
        except (OSError, RuntimeError) as exc:
            return str(exc)
    else:
        ap.print_help()
        return "\nNo pattern file or port patterns given on command line. Nothing to do."

    try:
        if args.actions:
            matchmaker.connect(max_attempts=1)

            if 'list_outs' in args.actions:
                matchmaker.list_ports(jacklib.JackPortIsOutput, include_aliases=args.aliases,
                                      include_pretty_names=args.pretty_names)
            if 'list_ins' in args.actions:
                matchmaker.list_ports(jacklib.JackPortIsInput, include_aliases=args.aliases,
                                      include_pretty_names=args.pretty_names)
            if 'list_cnx' in args.actions:
                matchmaker.list_connections(args.patterns)
        else:
            matchmaker.run()
    except KeyboardInterrupt:
        print('')
    except Exception as exc:
        if args.verbosity == 'DEBUG':
            log.exception("Startup error")
        else:
            log.error("Startup error: %s", exc)
        return str(exc)
    finally:
        matchmaker.close()


if __name__ == '__main__':
    sys.exit(main() or 0)
