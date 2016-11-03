# -*- coding: utf-8 -*-
"""Auto-connect new JACK ports matching the patterns given on the command line."""

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import logging
import re
import signal
import sys

from collections import defaultdict
from functools import lru_cache
from itertools import chain

try:
    import queue
except ImportError:
    import Queue as queue

from . import jacklib
from .jacklib_helpers import get_jack_status_error_string
from .version import __version__  # noqa


log = logging.getLogger("jack-matchmaker")


def pairwise(iterable):
    """s -> (s0,s1), (s2,s3), (s4, s5), ..."""
    args = [iter(iterable)] * 2
    return zip(*args)


def flatten(nestedlist):
    """Flatten one level of nesting."""
    return chain.from_iterable(nestedlist)


class JackMatchmaker(object):
    def __init__(self, patterns, pattern_file=None, name="jack-matchmaker"):
        self.patterns = []
        self.pattern_file = pattern_file

        if self.pattern_file:
            self.add_patterns_from_file(self.pattern_file)

            if not sys.platform.startswith('win'):
                signal.signal(signal.SIGHUP, self.reread_pattern_file)
            else:
                log.warning("Signal handling not supported on Windows. jack-matchmaker must be "
                            "restarted to re-read the pattern file.")

        for pair in patterns:
            self.add_patterns(*pair)

        self.queue = queue.Queue()
        status = jacklib.jack_status_t()
        self.client = jacklib.client_open("jack-matchmaker", jacklib.JackNoStartServer, status)
        err = get_jack_status_error_string(status)

        if err:
            raise RuntimeError(err)
        else:
            log.debug("Client connected, UUID: %s", jacklib.client_get_uuid(self.client))

    def close(self):
        jacklib.deactivate(self.client)
        return jacklib.client_close(self.client)

    def add_patterns(self, ptn_output, ptn_input):
        try:
            ptn_output = re.compile(ptn_output)
        except re.error as exc:
            log.error("Error in output port pattern '%s': %s", ptn_output, exc)
        else:
            if not (ptn_output, ptn_input) in self.patterns:
                log.debug("Added patterns: '%s' --> '%s'", ptn_output.pattern, ptn_input)
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
        except (IOError, OSError) as ec:
            log.error("Could not read '%s': %s", self.pattern_file, exc)
        else:
            self.reg_callback()

    def reg_callback(self, port_id=None, action=1, *args):
        if action == 0:
            return

        if port_id is not None:
            port = jacklib.port_by_id(self.client, port_id)
            log.debug("New port: %s", jacklib.port_name(port))

        inputs = list(flatten(self.get_ports(jacklib.JackPortIsInput)))
        outputs = list(flatten(self.get_ports(jacklib.JackPortIsOutput)))

        for ptn_output, ptn_input in self.patterns:
            for output in outputs:
                log.debug("Match regex '%s' on output '%s'.", ptn_output.pattern, output)
                match_output = ptn_output.match(output)
                if match_output:
                    log.debug("Found matching output port: %s.", output)
                    for input in inputs:
                        # try to fill-in groups matches from output port
                        # pattern into input port pattern
                        subst = defaultdict(str, **match_output.groupdict())
                        rx_input = ptn_input.format_map(subst)

                        log.debug("Match regex '%s' on input '%s'.", ptn_input, input)

                        try:
                            rx_input = re.compile(rx_input)
                        except re.error as exc:
                            log.error("Error in input port pattern '%s': %s", rx_input, exc)
                        else:
                            match_input = rx_input.match(input)
                            if match_input:
                                log.debug("Found matching input port: %s.", input)
                                self.queue.put((output, input))

    @lru_cache()
    def _get_port(self, name):
        return jacklib.port_by_name(self.client, name)

    def _get_aliases(self, port_name):
        port = self._get_port(port_name)
        num_aliases, *aliases = jacklib.port_get_aliases(port)
        return list(aliases[:num_aliases])

    def get_ports(self, type_=jacklib.JackPortIsOutput, include_aliases=True):
        for port_name in jacklib.get_ports(self.client, '', '', type_):
            if port_name is None:
                break

            port_name = port_name.decode('utf-8')

            if include_aliases:
                yield [port_name] + self._get_aliases(port_name)
            else:
                yield [port_name]

    def list_connections(self, include_aliases=True):
        raise NotImplementedError("Feature not implemented yet.")

    def list_ports(self, include_aliases=True):
        print(self._format_ports(self.get_ports(jacklib.JackPortIsOutput, include_aliases),
                                 'OUT: '))
        print(self._format_ports(self.get_ports(jacklib.JackPortIsOutput, include_aliases),
                                 'IN:  '))

    def _format_ports(self, ports, prefix):
        out = []
        for output in ports:
            out.append("%s%s" % (prefix, output[0]))

            for alias in output[1:]:
                out.append("     %s" %alias)

        return "\n".join(out)

    def run(self):
        jacklib.set_port_registration_callback(self.client, self.reg_callback, None)
        jacklib.activate(self.client)
        # call on-connection callback once to connect existing clients
        self.reg_callback()

        while True:
            try:
                output, input = self.queue.get(timeout=1)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                return
            else:
                if not jacklib.port_connected_to(self._get_port(output), input):
                    log.info("Connecting ports '%s' --> '%s'.", output, input)
                    jacklib.connect(self.client, output, input)


def main(args=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('-a', '--aliases', action="store_true",
                    help="Include aliases when listing ports")
    ap.add_argument('-l', '--list-ports', action="store_true",
                    help="List all JACK input and output ports")
    ap.add_argument('-c', '--list-connections', action="store_true",
                    help="List all connections between JACK ports")
    ap.add_argument('-p', '--pattern-file', metavar="FILE",
                    help="Read pattern pairs from FILE (one pattern per line)")
    ap.add_argument('-v', '--verbose', action="store_true", help="Be verbose")
    ap.add_argument('patterns', nargs='*', help="Port pattern pairs")
    args = ap.parse_args(args if args is not None else sys.argv[1:])

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s: %(message)s")

    if args.patterns and args.pattern_file:
        log.warning("Port pattern pairs from command line will be discarded when pattern file is "
                    "re-read on HUP signal.")

    if not any((args.patterns, args.pattern_file, args.list_ports, args.list_connections)):
        ap.print_help()
        return "\nNo pattern file or port patterns given on command line. Nothing to do."

    try:
        matchmaker = JackMatchmaker(pairwise(args.patterns), args.pattern_file)
    except RuntimeError as exc:
        return str(exc)

    try:
        if args.list_ports:
            matchmaker.list_ports(include_aliases=args.aliases)
        elif args.list_connections:
            matchmaker.list_connections()
        else:
            matchmaker.run()
    except Exception as exc:
        return str(exc)
    finally:
        matchmaker.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
