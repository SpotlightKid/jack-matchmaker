#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import sys
from jackmatchmaker import main


sys.exit(main(sys.argv[1:]) or 0)
