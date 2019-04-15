#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from jackmatchmaker import jacklib
from jackmatchmaker.jacklib_helpers import get_jack_status_error_string


status = jacklib.jack_status_t()
client = jacklib.client_open("list-all-properties", jacklib.JackNoStartServer, status)

if status:
    err = get_jack_status_error_string(status)
    sys.exit("Error connecting to JACK server: %s" % err)

properties = jacklib.get_all_properties()

for subject, props in properties.items():
    print("Subject %s:" % subject)

    for prop in props:
        print("* {p.key}: {p.value} (type: {p.type})".format(p=prop))

    print('')

jacklib.client_close(client)
