#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from itertools import chain

from jackmatchmaker import jacklib
from jackmatchmaker.jacklib_helpers import get_jack_status_error_string


status = jacklib.jack_status_t()
client = jacklib.client_open("list-port-info", jacklib.JackNoStartServer, status)

if status:
    err = get_jack_status_error_string(status)
    sys.exit("Error connecting to JACK server: %s" % err)

print("Output ports:\n")
for portname in jacklib.get_ports(client, '', '', jacklib.JackPortIsOutput):
    if portname is None:
        break

    portname = portname.decode('utf-8')
    port = jacklib.port_by_name(client, portname)
    uuid = jacklib.port_uuid(port)

    print("Port %s\nUUID: %s" % (portname, uuid))
    num_aliases, *aliases = jacklib.port_get_aliases(port)
    print("Aliases: %s" % ", ".join(aliases[:num_aliases]))

    props = jacklib.get_port_properties(client, portname)
    if props:
        print("Properties:")
        for prop in props:
            print(" * {}: {} (type: {})".format(prop.key, prop.value, prop.type))

    pretty_name = jacklib.get_port_pretty_name(client, portname)
    if pretty_name:
        print("Pretty-name: {}".format(pretty_name))

    print('')

print("\nInput ports:\n")
for portname in jacklib.get_ports(client, '', '', jacklib.JackPortIsInput):
    if portname is None:
        break

    portname = portname.decode('utf-8')
    port = jacklib.port_by_name(client, portname)
    uuid = jacklib.port_uuid(port)

    print("Port %s\nUUID: %s" % (portname, uuid))
    print("Aliases: %s" % ", ".join(aliases[:num_aliases]))

    props = jacklib.get_port_properties(client, portname)
    if props:
        print("Properties:")
        for prop in props:
            print(" * {}: {} (type: {})".format(prop.key, prop.value, prop.type))

    pretty_name = jacklib.get_port_pretty_name(client, portname)
    if pretty_name:
        print("Pretty-name: {}".format(pretty_name))

    print('')

jacklib.client_close(client)
