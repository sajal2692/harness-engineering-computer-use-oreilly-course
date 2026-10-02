"""Printing: every line starts with a tag for the part of the loop it comes from. Colors show in a terminal."""

import os
import sys

COLORS = {"e2b": "90", "exec": "90", "bash": "32", "screen": "32", "scale": "33", "thinking": "36",
          "claude": "1;36", "result": "37", "step": "1;35", "stopped": "33", "record": "90", "route": "1;33",
          "blocked": "1;31", "approval": "1;35", "check": "1;32"}


def tagged(tag, text):
    label = f"[{tag}]".ljust(11)
    if sys.stdout.isatty() and "NO_COLOR" not in os.environ:
        label = f"\033[{COLORS[tag]}m{label}\033[0m"
    return label + str(text).strip().replace("\n", "\n" + " " * 11)
