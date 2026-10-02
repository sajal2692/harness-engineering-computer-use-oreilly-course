"""Call Demo 1's tools directly on the Docker desktop, the way Claude would, and check each step.

Counts the receipts with bash, clicks the Applications menu, types a note into the text editor, saves it through the
Save As dialog, and reads it back with the file tool. Also checks the session keeps cd, a timeout restarts it, and the harness refuses a click off
the screenshot and a file outside the home folder. Runs the container for about a minute and calls no model.
"""

import contextlib
import io
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

DEMO = Path(__file__).resolve().parents[1] / "demos" / "01_building_computer_tools"
sys.path.insert(0, str(DEMO))

import desktop  # noqa: E402
import shell  # noqa: E402
from tools import run_tool  # noqa: E402

failures = []


def call(name, settle=0.0, computer=False, **args):
    """Run one tool call the way the agent loop does, and return its result as text plus everything it printed."""
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        content, is_error = run_tool(SimpleNamespace(name=name, input=args, toolset_name="computer" if computer else None))
    time.sleep(settle)
    text = content if isinstance(content, str) else "an image"
    output = printed.getvalue() + ("error " if is_error else "") + text
    print(f"> {name} {args}\n{output}")
    return output


def check(label, condition):
    print(f"{'PASS' if condition else 'FAIL'}  {label}\n")
    if not condition:
        failures.append(label)


desktop.start()
shell.start_session()

count = call("bash", command="ls receipts | wc -l")
check("bash counts the four receipts and reports the exit status", "exit status 0" in count and count.rstrip().endswith("4"))
call("bash", command="cd receipts")
check("the session keeps the working directory between commands", "/home/agent/receipts" in call("bash", command="pwd"))
check("a failing command reports its exit status", "exit status 2" in call("bash", command="ls missing_folder"))

shell.TIMEOUT = 3
waited = call("bash", command="cat")  # waits for input that never comes
check("a command that waits for input times out and the session restarts", "timeout:" in waited)
check("the new session starts in the home folder again", "/home/agent\n" in call("bash", command="pwd") + "\n")
shell.TIMEOUT = 30

shot = call("screenshot", computer=True)
check("a screenshot is captured at 2560 x 1440 and scaled to 1280 x 720", "captured 2560 x 1440" in shot and "1,196" in shot)
check("a click off the screenshot sends no input", "out of bounds" in call("left_click", computer=True, coordinate=[1400, 100]))
menu = call("left_click", settle=1.5, computer=True, coordinate=[50, 12])
check("a click is scaled to the display and sent with xdotool", "(100, 24) on the display" in menu and "xdotool click" in menu)
call("key", computer=True, text="Escape")
subprocess.run(["docker", "exec", "-d", desktop.CONTAINER, "mousepad"])  # the test opens the editor directly
time.sleep(4)
check("the text editor opens on the Xfce desktop", "Mousepad" in desktop.run(["wmctrl", "-l"], quiet=True).stdout)
call("left_click", computer=True, coordinate=[640, 360])
call("type", computer=True, text="There are 4 receipts.")
call("key", settle=2.0, computer=True, text="ctrl+s")
call("screenshot", computer=True)
call("key", computer=True, text="ctrl+a")
call("type", settle=1.0, computer=True, text="/home/agent/notes/receipt_count.txt")
call("key", settle=2.0, computer=True, text="Return")

saved = call("str_replace_based_edit_tool", command="view", path="~/notes/receipt_count.txt")
check("the note saved through the Save As dialog reads back through the file tool", "There are 4 receipts." in saved)
check("the file tool refuses a path outside the home folder",
      "outside /home/agent" in call("str_replace_based_edit_tool", command="view", path="/etc/passwd"))
zoomed = call("zoom", computer=True, region=[0, 0, 320, 180])
check("zoom returns a full-detail crop", "zoomed into" in zoomed and "640 x 360" in zoomed)

print("All checks passed" if not failures else f"{len(failures)} checks failed: {failures}")
sys.exit(1 if failures else 0)  # the container is removed on exit
