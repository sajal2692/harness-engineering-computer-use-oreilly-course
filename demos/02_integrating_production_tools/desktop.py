"""The agent's computer: an E2B Desktop sandbox in the cloud, created for this run and deleted at the end.

It starts from the template that template.py builds: E2B's desktop plus the GnuCash accounting app."""

import atexit
import sys
import time
from pathlib import Path

from e2b_desktop import Sandbox

from output import tagged

TEMPLATE = "computer-use-course-gnucash"
HOME = "/home/user"
BOOKS = f"{HOME}/books/lakeview.gnucash"
FILES = Path(__file__).parent
SANDBOX_ID = FILES / ".sandbox_id"  # tells watch.py which desktop to follow
RESOLUTION = (1280, 720)  # the same size as the screenshots Claude gets, so clicks need no scaling
sandbox = None  # the E2B Desktop sandbox, made by start()


# 1. start: create a fresh desktop with no internet access, upload the task's files, and start the live view.
#    E2B gives us what Demo 1 built by hand: the virtual display, the desktop, the viewer, and files in and out.
def start():
    global sandbox
    started = time.time()
    try:
        sandbox = Sandbox.create(template=TEMPLATE, resolution=RESOLUTION, timeout=1800, allow_internet_access=False)
    except Exception as error:  # a missing key, no template yet, or no network
        sys.exit(f"[error] Could not create the E2B desktop: {error}. Check E2B_API_KEY, and run template.py once.")
    atexit.register(stop)
    SANDBOX_ID.write_text(sandbox.sandbox_id)
    print(tagged("e2b", f"desktop {sandbox.sandbox_id} ready in {time.time() - started:.1f} seconds, "
                        f"{RESOLUTION[0]} x {RESOLUTION[1]}, internet access off"))

    # 2. The invoices to process, the finance records, and the company's books
    for folder in ("inbox", "finance", "books"):
        for file in sorted((FILES / folder).iterdir()):
            sandbox.files.write(f"{HOME}/{folder}/{file.name}", file.read_bytes())
    sandbox.files.make_dir(f"{HOME}/work")
    # The finance records are master data: owned by root and read-only, so the agent's account cannot change them
    sandbox.commands.run(f"chown -R root:root {HOME}/finance && chmod 755 {HOME}/finance && chmod 444 {HOME}/finance/*",
                         user="root")
    print(tagged("e2b", "uploaded 8 invoices to ~/inbox, purchase orders and vendors to ~/finance (read-only), "
                        "and the books to ~/books"))
    sandbox.stream.start()
    print(tagged("e2b", f"watch it here (you can also take over): {sandbox.stream.get_url()}"))


# 3. open_books: start GnuCash with the company's books, full screen. The harness does this only after approval.
def open_books():
    sandbox.commands.run(f"setsid gnucash {BOOKS} >/dev/null 2>&1 &")
    for _ in range(60):  # wait for the main window with the books, not the splash screen
        if "lakeview.gnucash" in sandbox.commands.run("xdotool search --name GnuCash getwindowname %@ || true").stdout:
            break
        time.sleep(1)
    sandbox.commands.run("xdotool search --name 'lakeview.gnucash' windowmove 0 28 windowsize 1280 645 || true")
    print(tagged("e2b", "GnuCash is open with the books"))


def stop():
    sandbox.kill()
    SANDBOX_ID.unlink(missing_ok=True)
    print(tagged("e2b", "desktop deleted"))
