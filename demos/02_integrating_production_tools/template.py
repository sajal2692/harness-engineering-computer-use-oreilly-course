"""Build the E2B template this demo uses: E2B's desktop with GnuCash and sqlite3 installed. Run once before the demo.

uv run template.py
"""

from dotenv import load_dotenv
from e2b import Template

load_dotenv()  # reads E2B_API_KEY from the .env file at the top of the repository

NAME = "computer-use-course-gnucash"

# E2B's own desktop template, plus a desktop accounting app, its SQLite storage driver, and the SQLite command line
# to query its books. GnuCash's tip of the day is switched off so it does not cover the window at start.
template = (Template().from_template("desktop")
            .apt_install(["gnucash", "libdbd-sqlite3", "sqlite3"])
            .run_cmd("dbus-run-session gsettings set org.gnucash.GnuCash.dialogs.totd show-at-startup false || true",
                     user="user"))

Template.build(template, NAME, cpu_count=2, memory_mb=4096,
               on_build_logs=lambda entry: print(entry.message if hasattr(entry, "message") else entry, flush=True))
print(f"Built the E2B template {NAME}")
