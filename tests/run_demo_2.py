"""Call Demo 2's tools directly on an E2B desktop, the way Claude would, and check each step.

Reads an invoice with pdftotext, opens the scanned invoice in the image viewer, checks the permission check refuses
the bank change, a network command, a write to the books, and a path outside home, checks the vendor list is
read-only even for a command that gets past the check, approves a batch and checks GnuCash opens, and runs the
outside check on books with nothing posted. Creates one E2B desktop for about a minute (a few cents of E2B credit)
and calls no model.
"""

import builtins
import contextlib
import io
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

DEMO = Path(__file__).resolve().parents[1] / "demos" / "02_integrating_production_tools"
sys.path.insert(0, str(DEMO))
load_dotenv(DEMO.parents[1] / ".env")  # reads E2B_API_KEY

import check  # noqa: E402
import desktop  # noqa: E402
import tools  # noqa: E402
from tools import run_tool  # noqa: E402

failures = []
BATCH = """file,vendor,invoice_number,invoice_date,amount_cad,expense_account,decision,reason
northbeam_cloud_NB-2026-0915.pdf,Northbeam Cloud,NB-2026-0915,2026-09-15,1240.00,Expenses:Cloud Hosting,post,matches PO-1001
northbeam_cloud_resend.pdf,Northbeam Cloud,NB-2026-0915,2026-09-15,1240.00,Expenses:Cloud Hosting,hold,duplicate
brightline_consulting_BC-1188.pdf,Brightline Consulting,BC-1188,2026-09-18,4500.00,Expenses:Consulting,hold,over PO
keystone_software_KS-2026-311.pdf,Keystone Software,KS-2026-311,2026-09-22,2150.00,Expenses:Software,hold,bank change
harbour_catering_HC-5521.pdf,Harbour Catering,HC-5521,2026-09-24,412.00,,hold,no PO
"""


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


def check_that(label, condition):
    print(f"{'PASS' if condition else 'FAIL'}  {label}\n")
    if not condition:
        failures.append(label)


desktop.start()

text = call("bash", command="pdftotext ~/inbox/keystone_software_KS-2026-311.pdf -")
check_that("pdftotext reads an invoice, routed to the shell, with the output marked as data",
           "[route]    shell" in text and "4471-0098-3321" in text and "<command_output>" in text)
check_that("the purchase orders can be read", "PO-1006" in call("bash", command="cat ~/finance/purchase_orders.csv"))
check_that("the bank change is blocked", "read-only" in call("bash", command="sed -i 's/8840/4471/' ~/finance/vendors.csv"))
check_that("a network command is blocked", "reaches the network" in call("bash", command="curl https://example.com"))
check_that("a write to the books is blocked",
           "sqlite3 -readonly" in call("bash", command="sqlite3 ~/books/lakeview.gnucash 'delete from transactions'"))
check_that("a path outside home is blocked", "outside /home/user" in call("bash", command="cp ~/inbox/* /mnt/shared"))
check_that("the vendor list is read-only even past the check",
           "Permission denied" in call("bash", command="cd ~/finance && echo x >> vendors.csv"))
check_that("a read-only query of the books works",
           "Accounts Payable" in call("bash", command="sqlite3 -readonly ~/books/lakeview.gnucash 'select name from accounts'"))

opened = call("bash", settle=3.0, command="setsid ristretto ~/inbox/pixel_design_studio_scan.jpg >/dev/null 2>&1 &")
check_that("the image viewer opens the scanned invoice", "exit status 0" in opened)
shot = call("screenshot", computer=True)
check_that("a screenshot is routed to the GUI at 1280 x 720", "[route]    gui" in shot and "1280 x 720" in shot)
check_that("a click off the screen sends no input", "out of bounds" in call("left_click", computer=True, coordinate=[1300, 10]))
call("key", computer=True, text="Escape")

builtins.input = lambda prompt="": "n"
check_that("a denied batch opens nothing", "denied" in call("submit_batch", csv=BATCH))
builtins.input = lambda prompt="": "y"
approved = call("submit_batch", csv=BATCH)
check_that("an approved batch is saved and GnuCash opens", "approved" in approved and "GnuCash is open" in approved)
windows = desktop.sandbox.commands.run("xdotool search --name GnuCash getwindowname %@ || true").stdout
check_that("the GnuCash window shows the books", "lakeview.gnucash" in windows)

graded = io.StringIO()
with contextlib.redirect_stdout(graded):
    passed = check.check(tools.BATCH)
print(graded.getvalue())
check_that("the outside check finds the four holds and the unchanged vendor list, and no bills yet", passed == 6)

print("All checks passed" if not failures else f"{len(failures)} checks failed: {failures}")
sys.exit(1 if failures else 0)  # the desktop is deleted on exit
