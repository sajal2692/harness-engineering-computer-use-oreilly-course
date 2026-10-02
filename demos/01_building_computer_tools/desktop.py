"""The agent's computer: start the Docker desktop, run programs inside it, and remove it on exit."""

import atexit
import subprocess
import sys
import time
from pathlib import Path

from output import tagged

IMAGE = "computer-use-demo1"
CONTAINER = "computer-use-demo1"
VIEWER = "http://localhost:6080/vnc.html?autoconnect=1&resize=scale"


# 1. start: build the image, run a new container, and wait until the Xfce desktop is up
def start():
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        sys.exit("[error] Docker is not running. Start Docker Desktop and try again.")
    print(tagged("docker", f"building the image {IMAGE} (fast after the first time)"))
    subprocess.run(["docker", "build", "-q", "-t", IMAGE, str(Path(__file__).parent)], check=True, capture_output=True)
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)  # a container left from an earlier run
    subprocess.run(["docker", "run", "-d", "--rm", "--name", CONTAINER, "-p", "127.0.0.1:6080:6080", IMAGE],
                   check=True, capture_output=True)
    atexit.register(stop)
    started = time.time()
    while "xfce4-panel" not in run(["wmctrl", "-l"], quiet=True).stdout:
        if time.time() - started > 60:
            sys.exit("[error] The desktop did not start within 60 seconds. Run: docker logs " + CONTAINER)
        time.sleep(0.5)
    size = run(["xdotool", "getdisplaygeometry"], quiet=True).stdout.split()
    print(tagged("docker", f"desktop ready in {time.time() - started:.1f} seconds: a {size[0]} x {size[1]} display, "
                           f"Xfce with no application open, 4 files in ~/receipts"))
    print(tagged("docker", f"watch it here: {VIEWER}"))


def stop():
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True)
    print(tagged("docker", "container removed"))


# 2. run: run one program inside the desktop, as the agent's user, and return what it printed
def run(command, quiet=False, binary=False):
    if not quiet:
        print(tagged("exec", " ".join(command)))
    return subprocess.run(["docker", "exec", CONTAINER, *command], capture_output=True, text=not binary, timeout=30)
