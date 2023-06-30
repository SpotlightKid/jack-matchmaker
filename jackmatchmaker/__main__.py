#!/usr/bin/env python

import sys
from . import main


sys.exit(main(sys.argv[1:]) or 0)
