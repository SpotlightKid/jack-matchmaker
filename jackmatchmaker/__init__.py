# -*- coding: utf-8 -*-
"""Auto-connect new JACK ports matching the patterns given on the command line."""

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import logging
import re
import sys

try:
    import queue
except ImportError:
    import Queue as queue

from . import jacklib

log = logging.getLogger("jack-matchmaker")


def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    args = [iter(iterable)] * 2
    return zip(*args)


class JackMatchmaker(object):
    def __init__(self, patterns, name="jack-matchmaker"):
        self.patterns = patterns
        log.debug("Patterns: %s", self.patterns)
        self.client = jacklib.client_open("jack-matchmaker", jacklib.JackNoStartServer, None)
        jacklib.set_port_registration_callback(self.client, self.reg_callback, None)
        jacklib.activate(self.client)
        self.queue = queue.Queue()

    def close(self):
        jacklib.deactivate(self.client)
        return jacklib.client_close(self.client)

    def reg_callback(self, port_id, action, *args):
        if action == 0:
            return

        inputs = self.get_ports_and_aliases(jacklib.JackPortIsInput)
        log.debug("Inputs:\n%s", "\n".join(inputs))
        outputs = self.get_ports_and_aliases(jacklib.JackPortIsOutput)
        log.debug("Outputs:\n%s", "\n".join(outputs))

        for left, right in self.patterns:
            for output in outputs:
                log.debug("Checking output '%s' against pattern '%s'.", output, left)
                match = re.match(left, output, re.I)
                if match:
                    log.info("Found matching output port: %s.", output)
                    for input in inputs:
                        log.debug("Checking input '%s' against pattern '%s'.", input, right)
                        match = re.match(right, input, re.I)
                        if match:
                            log.info("Found matching input port: %s.", input)
                            self.queue.put((output, input))

    def get_ports_and_aliases(self, type_=jacklib.JackPortIsOutput):
        ports = []
        for port_name in jacklib.get_ports(self.client, '', '', type_):
            if port_name is None:
                break

            port_name = port_name.decode('utf-8')
            ports.append(port_name)

            port = jacklib.port_by_name(self.client, port_name)
            aliases = jacklib.port_get_aliases(port)
            if aliases[0]:
                for i in range(aliases[0]):
                    ports.append(aliases[i+1])

        return ports

    def run(self):
        try:
            while True:
                try:
                    output, input = self.queue.get(timeout=1)
                except queue.Empty:
                    pass
                else:
                    log.info("Connecting ports '%s' <-> '%s'.", output, input)
                    jacklib.connect(self.client, output, input)
        finally:
            return self.close()


def main(args=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('-v', '--verbose', action="store_true", help="Be verbose")
    ap.add_argument('patterns', nargs='*', help="Port pattern pairs")
    args = ap.parse_args(args if args is not None else sys.argv[1:])

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="[%(name)s] %(levelname)s: %(message)s")

    matchmaker = JackMatchmaker(list(pairwise(args.patterns)))
    matchmaker.run()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
