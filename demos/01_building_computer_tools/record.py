"""The run record: a trail of what Claude saw, what it asked for, and what came back, saved under runs/.

Open trail.md with a Markdown preview to read the run turn by turn, with each screenshot Claude received."""

import base64
import json
from datetime import datetime
from pathlib import Path

from output import tagged

folder = None  # runs/<date-time>/, made by start()
images = 0


def write(text):
    with open(folder / "trail.md", "a") as trail:
        trail.write(text + "\n")


# 1. start: a new folder for this run, and the task at the top of the trail
def start(task):
    global folder
    folder = Path(__file__).parent / "runs" / f"{datetime.now():%Y-%m-%d_%H-%M-%S}"
    folder.mkdir(parents=True)
    write(f"# Run record\n\n**Task:** {task}\n")
    print(tagged("record", f"run record: {folder.relative_to(Path(__file__).parent) / 'trail.md'}"))


# 2. turn: what Claude read and wrote, and what it said or thought, at the start of each turn
def turn(number, usage, notes):
    write(f"## Turn {number}\n\n{usage}\n")
    for note in notes:
        write("> " + note.strip().replace("\n", "\n> ") + "\n")


# 3. call: one tool call and its result. A screenshot is saved as the exact image Claude received.
def call(name, args, content, is_error):
    global images
    write(f"- **{name}** `{json.dumps(args)}`")
    if isinstance(content, str):
        status = "error: " if is_error else ""
        lines = content.splitlines() or [""]
        write("  ```text\n  " + status + "\n  ".join(lines[:20]) + ("\n  ..." if len(lines) > 20 else "") + "\n  ```")
        return
    images += 1
    path = f"{images:03}_{name}.png"
    (folder / path).write_bytes(base64.b64decode(content[0]["source"]["data"]))
    write(f"\n  ![{name} {images}]({path})\n")
