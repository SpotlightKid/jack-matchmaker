#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from jackmatchmaker import jacklib
from jackmatchmaker.jacklib_helpers import get_jack_status_error_string


if sys.argv[1:]:
    portname = sys.argv[1]
else:
    sys.exit("Usage: %s <port name>" % sys.argv[0])

status = jacklib.jack_status_t()
client = jacklib.client_open("list-all-port-properties", jacklib.JackNoStartServer, status)

if status:
    err = get_jack_status_error_string(status)
    sys.exit("Error connecting to JACK server: %s" % err)

properties = jacklib.get_port_properties(client, portname)

for prop in properties:
    print("{p.key}: {p.value} (type: {p.type})".format(p=prop))

jacklib.client_close(client)
