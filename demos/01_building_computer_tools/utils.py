"""Display helper for the audience, not a tool Claude can call: the --step preview of what Claude is about to do."""

import desktop
import gui
from output import tagged


# preview: with --step, move the pointer onto the point Claude chose, so the room sees the target in the viewer
# before the action runs. Typing and key presses have no point, so they are only described.
def preview(name, args):
    action = f'run "{args.get("command")}"' if name == "bash" else name.replace("_", " ")
    if name in ("type", "key"):
        action += f' "{args["text"]}"'.replace("\n", "\\n")
    if "coordinate" in args:
        x, y = args["coordinate"]
        desktop.run(["xdotool", "mousemove", str(round(x * gui.SCALE)), str(round(y * gui.SCALE))], quiet=True)
        action += f" at ({x}, {y}). The pointer is on the target"
    print(tagged("step", f"Claude wants to {action}"))
