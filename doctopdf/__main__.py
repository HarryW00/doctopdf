#!/usr/bin/env python3
"""
Entry point for `python -m doctopdf`.

Allows running the converter as a module:
    python -m doctopdf --input ./docs --output ./pdfs
"""

import sys

from .cli import main

sys.exit(main())
