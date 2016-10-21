# -*- coding: utf-8 -*-
"""Auto-connect new JACK ports matching the patterns given on the command line."""

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import logging
import re
import sys

from collections import defaultdict
from itertools import chain

try:
    import queue
except ImportError:
    import Queue as queue

from . import jacklib
from .jacklib_helpers import get_jack_status_error_string

log = logging.getLogger("jack-matchmaker")


def pairwise(iterable):
    """s -> (s0,s1), (s2,s3), (s4, s5), ..."""
    args = [iter(iterable)] * 2
    return zip(*args)


def flatten(nestedlist):
    """Flatten one level of nesting"""
    return chain.from_iterable(nestedlist)


class JackMatchmaker(object):
    def __init__(self, patterns, name="jack-matchmaker"):
        self.patterns = []
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
        except re.error:
            log.error("Error in output port pattern '%s': %s", ptn_output, exc)
        else:
            self.patterns.append((ptn_output, ptn_input))

    def reg_callback(self, port_id, action, *args):
        if action == 0:
            return

        inputs = list(flatten(self.get_ports(jacklib.JackPortIsInput)))
        log.debug("Inputs:\n%s", "\n".join(inputs))
        outputs = list(flatten(self.get_ports(jacklib.JackPortIsOutput)))
        log.debug("Outputs:\n%s", "\n".join(outputs))

        for ptn_output, ptn_input in self.patterns:
            for output in outputs:
                log.debug("Checking output '%s' against pattern '%s'.", output, ptn_output)
                match_output = ptn_output.match(output)
                if match_output:
                    log.debug("Found matching output port: %s.", output)
                    for input in inputs:
                        # try to fill-in groups matches from output port
                        # pattern into input port pattern
                        subst = defaultdict(str, **match_output.groupdict())
                        rx_input = ptn_input.format_map(subst)

                        log.debug("Checking input '%s' against pattern '%s'.", input, ptn_input)

                        try:
                            rx_input = re.compile(rx_input)
                        except re.error:
                            log.error("Error in input port pattern '%s': %s", rx_input, exc)
                        else:
                            match_input = rx_input.match(input)
                            if match_input:
                                log.debug("Found matching input port: %s.", input)
                                self.queue.put((output, input))

    def get_ports(self, type_=jacklib.JackPortIsOutput, include_aliases=True):
        for port_name in jacklib.get_ports(self.client, '', '', type_):
            if port_name is None:
                break

            port_name = port_name.decode('utf-8')

            if include_aliases:
                port = jacklib.port_by_name(self.client, port_name)
                num_aliases, *aliases = jacklib.port_get_aliases(port)
                yield [port_name] + list(aliases[:num_aliases])
            else:
                yield [port_name]

    def list_connections(self, include_aliases=True):
        raise NotImplementedError("Feature not implemented yet.")

    def list_ports(self, include_aliases=True):
        print("Inputs:\n")
        for input in self.get_ports(jacklib.JackPortIsInput, include_aliases):
            print(input[0])

            for alias in input[1:]:
                print("    %s" % alias)

        print("\nOutputs:\n")
        for output in self.get_ports(jacklib.JackPortIsOutput, include_aliases):
            print(output[0])

            for alias in output[1:]:
                print("    %s" % alias)

    def run(self):
        log.debug("Patterns: %s", self.patterns)
        jacklib.set_port_registration_callback(self.client, self.reg_callback, None)
        jacklib.activate(self.client)
        # call on-connection callback once to connect existing clients
        self.reg_callback('dummy', 1)

        while True:
            try:
                output, input = self.queue.get(timeout=1)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                return
            else:
                log.info("Connecting ports '%s' <-> '%s'.", output, input)
                jacklib.connect(self.client, output, input)


def main(args=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('-a', '--aliases', action="store_true",
                    help="Include aliases when listing ports")
    ap.add_argument('-l', '--list-ports', action="store_true",
                    help="List all JACK input and output ports")
    ap.add_argument('-c', '--list-connections', action="store_true",
                    help="List all connections between JACK ports")
    ap.add_argument('-v', '--verbose', action="store_true", help="Be verbose")
    ap.add_argument('patterns', nargs='*', help="Port pattern pairs")
    args = ap.parse_args(args if args is not None else sys.argv[1:])

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="[%(name)s] %(levelname)s: %(message)s")

    try:
        matchmaker = JackMatchmaker(list(pairwise(args.patterns)))
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
