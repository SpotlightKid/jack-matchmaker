#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from jackmatchmaker import jacklib
from jackmatchmaker.jacklib_helpers import get_jack_status_error_string


if len(sys.argv) == 3:
    portname = sys.argv[1]
    pretty_name = sys.argv[2]
else:
    sys.exit("Usage: %s <port name> <pretty-name>" % sys.argv[0])

status = jacklib.jack_status_t()
client = jacklib.client_open("set-port-pretty-name", jacklib.JackNoStartServer, status)

if status:
    err = get_jack_status_error_string(status)
    sys.exit("Error connecting to JACK server: %s" % err)

res = jacklib.set_port_pretty_name(client, portname, pretty_name)
if res != -1:
    print("Pretty name for port '%s' is now '%s'." % (portname, pretty_name))


jacklib.client_close(client)
