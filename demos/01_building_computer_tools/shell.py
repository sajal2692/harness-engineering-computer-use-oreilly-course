"""The shell tools: one long-lived bash session inside the desktop, and a file viewer."""

import os
import posixpath
import select
import subprocess
import time

import desktop
from output import tagged

HOME = "/home/agent"
TIMEOUT = 30  # seconds a command may run before the session is killed and restarted
MAX_LINES = 100  # lines of output the model gets; the rest is cut
DONE = "__command_done__"  # printed after every command, so the harness knows it finished
session = None  # the bash process, started by start_session()
group = None  # its process group inside the container, which a timeout kills


# 1. start_session: one bash process that stays alive between commands, so cd and variables carry over.
#    setsid puts bash and everything it starts in their own process group.
def start_session():
    global session, group
    command = ["docker", "exec", "-i", "-w", HOME, desktop.CONTAINER, "setsid", "--wait", "bash", "--norc"]
    print(tagged("exec", " ".join(command)))
    session = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    group = send("echo $$")[0].strip()
    print(tagged("bash", f"started a bash session in {HOME}, process group {group}"))


# 2. send: write the command to bash, then a line that prints the marker and the exit status. Read until the marker.
#    The marker is written in two quoted halves, so a command that echoes its input cannot fake it.
def send(command):
    written = f'{command}\necho "{DONE[:8]}""{DONE[8:]}" $?\n'
    print(tagged("exec", "to bash: " + written.rstrip().replace("\n", "\nto bash: ")))
    session.stdin.write(written.encode())
    session.stdin.flush()
    output, started = b"", time.time()
    while DONE.encode() not in output:
        waited = time.time() - started
        ready, _, _ = select.select([session.stdout], [], [], max(0, TIMEOUT - waited))
        if not ready:
            raise TimeoutError
        chunk = os.read(session.stdout.fileno(), 65536)
        if not chunk:
            raise RuntimeError("the bash session exited")
        output += chunk
    text, status = output.decode(errors="replace").rsplit(DONE, 1)
    print(tagged("exec", f"from bash: {len(text):,} characters, then the marker and exit status {status.split()[0]}"))
    return text, int(status.split()[0])


# 3. restart: kill bash and every process it started, then start a clean session
def restart():
    desktop.run(["kill", "-KILL", "--", f"-{group}"], quiet=True)
    session.kill()
    start_session()


# 4. bash: run one command in the session and return its output, exit status, and duration
def bash(command=None, restart_session=False):
    if restart_session:
        restart()
        return "The bash session was restarted."
    print(tagged("bash", f"$ {command}"))
    started = time.time()
    try:
        output, status = send(command)
    except TimeoutError:
        restart()
        return (f"timeout: the command ran for more than {TIMEOUT} seconds. The session was restarted, so earlier "
                "cd and variables are gone. Check which effects happened before running it again.")
    except RuntimeError:
        start_session()
        return "error: the bash session exited, for example because of exit. A new session was started."
    lines = output.rstrip("\n").splitlines()
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES] + [f"[{len(lines)} lines in all; only the first {MAX_LINES} are shown]"]
    return f"exit status {status}, {time.time() - started:.1f} seconds\n" + "\n".join(lines)


# 5. view: show a file with line numbers, or list a folder. Its path rule keeps it inside the agent's home folder.
def view(path, view_range=None):
    path = posixpath.normpath(posixpath.join(HOME, path.replace("~", HOME, 1)))
    if path != HOME and not path.startswith(HOME + "/"):
        return f"error: {path} is outside {HOME}, so the file tool will not open it."
    listing = desktop.run(["ls", "-1", path])
    if listing.returncode:
        return f"error: {listing.stderr.strip()}"
    if listing.stdout.strip() != path:  # ls prints a file's own path, and a folder's contents
        return f"{path} contains:\n{listing.stdout}"
    lines = desktop.run(["cat", "--", path]).stdout.splitlines()
    first, last = view_range or (1, len(lines))
    last = len(lines) if last == -1 else last
    return "\n".join(f"{number:6}\t{line}" for number, line in enumerate(lines[first - 1:last], start=first))
