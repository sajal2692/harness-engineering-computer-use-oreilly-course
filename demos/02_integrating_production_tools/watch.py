"""Follow the shell on the E2B desktop: every command Claude runs and its output, live, in a second terminal.

uv run watch.py     run in a second terminal while main.py runs. It waits for the desktop, then follows it.
"""

import sys
import time

from dotenv import load_dotenv
from e2b import Sandbox

import desktop
import shell

load_dotenv()  # reads E2B_API_KEY from the .env file at the top of the repository

# 1. Wait for main.py to create the desktop and save its id
print("Waiting for the desktop. Start main.py in another terminal.", flush=True)
while not desktop.SANDBOX_ID.exists():
    time.sleep(1)
sandbox = Sandbox.connect(desktop.SANDBOX_ID.read_text())
print(f"Following the shell on {sandbox.sandbox_id}. Ctrl-C to stop.\n", flush=True)

# 2. Follow the harness's log of commands inside the desktop, printing each line as it arrives
try:
    sandbox.commands.run(f"touch {shell.LOG}; tail -n +1 -F {shell.LOG} 2>/dev/null",
                         on_stdout=lambda line: print(line, end="", flush=True), timeout=0)
except KeyboardInterrupt:
    pass
except Exception:  # the desktop was deleted at the end of the run
    print("\nThe desktop was deleted.")
sys.exit(0)
