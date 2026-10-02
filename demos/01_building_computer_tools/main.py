"""Demo 1: shell and GUI tools built from docker exec, bash, ImageMagick, and xdotool, used by Claude on a Linux desktop.

uv run main.py            Claude does the task
uv run main.py --step     Claude does the task, and you press Enter at each hand-off
"""

import os
import signal
import sys

from dotenv import load_dotenv

import agent
import desktop
import record
import shell
from output import tagged

load_dotenv()  # reads ANTHROPIC_API_KEY from the .env file at the top of the repository
TASK = ("Count the receipt files in ~/receipts with a command. Then open the text editor, type a one-line note "
        "with the count, and save it as ~/notes/receipt_count.txt. Finally, read the saved file with the file tool "
        "to check it.")
SYSTEM = ("You work on a Debian Linux desktop with Xfce. The Applications menu at the top left lists the installed "
          "applications; the text editor is Mousepad. Use the bash tool for commands and the text editor tool to "
          "read files. Use the computer tools to operate applications on screen: take a screenshot before you act, "
          "and end each group of actions with a screenshot so you can check the result. Keyboard shortcuts are "
          "often more reliable than small targets. Report only what you checked.")

# 1. Stop early if the API key is missing, and stop cleanly on Ctrl-C (the container is still removed)
if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("[error] ANTHROPIC_API_KEY is not set. Copy .env.example to .env at the top of the repository.")
signal.signal(signal.SIGINT, lambda *args: sys.exit("\n[stopped] Ctrl-C"))

# 2. Start the desktop and the bash session inside it
desktop.start()
shell.start_session()

# 3. Wait until you have the viewer open, then Claude does the task with the shell and GUI tools.
#    With --step, the loop's own first pause does this.
step = "--step" in sys.argv
if not step and sys.stdin.isatty():
    input("\nOpen the viewer link above, then press Enter to start. ")
agent.run(TASK, SYSTEM, step=step)

# 4. Point to the run record, and keep the desktop open until you press Enter
print(tagged("record", f"every screenshot Claude saw and every call it made: {record.folder}/trail.md"))
if sys.stdin.isatty():
    input("\nPress Enter to remove the desktop. ")
