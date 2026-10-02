"""The shell tools on E2B: each command runs in a fresh process through E2B's commands API, and a file viewer.

Demo 1 kept one bash process alive and read until a marker. E2B returns the exit code, stdout, and stderr directly."""

import posixpath
import time

from e2b import CommandExitException, TimeoutException

import desktop
from output import tagged

WORK = f"{desktop.HOME}/work"
TIMEOUT = 30  # seconds a command may run
MAX_LINES = 100  # lines of output the model gets; the rest is cut
LOG = "/tmp/harness_shell.log"  # every command and its output, for watch.py. Outside the folders Claude may use.
log = ""


def write_log(text):
    global log
    log += text
    desktop.sandbox.files.write(LOG, log, user="root")  # root owns it, so Claude's commands cannot change it


# 1. bash: run one command in ~/work and return its exit status, duration, and output.
#    The output is marked as data, so text inside a file cannot pose as an instruction from the harness.
def bash(command):
    print(tagged("bash", f"$ {command}"))
    write_log(f"\n$ {command}\n")
    started = time.time()
    try:
        result = desktop.sandbox.commands.run(command, cwd=WORK, timeout=TIMEOUT)
    except CommandExitException as result_with_error:  # a non-zero exit is a result, not a crash
        result = result_with_error
    except TimeoutException:
        write_log(f"[timeout after {TIMEOUT} seconds]\n")
        return f"timeout: the command ran for more than {TIMEOUT} seconds and was stopped."
    write_log(result.stdout + result.stderr + f"[exit status {result.exit_code}]\n")
    lines = (result.stdout + result.stderr).rstrip("\n").splitlines()
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES] + [f"[{len(lines)} lines in all; only the first {MAX_LINES} are shown]"]
    return (f"exit status {result.exit_code}, {time.time() - started:.1f} seconds\n"
            "<command_output>\n" + "\n".join(lines) + "\n</command_output>")


# 2. view: show a file with line numbers. Its path rule keeps it inside the agent's home folder.
def view(path, view_range=None):
    path = posixpath.normpath(posixpath.join(desktop.HOME, path.replace("~", desktop.HOME, 1)))
    if not path.startswith(desktop.HOME + "/"):
        return f"error: {path} is outside {desktop.HOME}, so the file tool will not open it."
    try:
        lines = desktop.sandbox.files.read(path).splitlines()
    except Exception as error:
        return f"error: {error}"
    first, last = view_range or (1, len(lines))
    last = len(lines) if last == -1 else last
    numbered = "\n".join(f"{number:6}\t{line}" for number, line in enumerate(lines[first - 1:last], start=first))
    return f"<file_content>\n{numbered}\n</file_content>"
