"""Display helpers for the audience, not tools Claude can call: the --step preview of what Claude is about to do, and
the frame that shows the room what it just did."""

import shlex

import desktop
import gui
from output import tagged

# The frame, a small Tk program run on the desktop: four red strips around an area, and a label, for 0.6 seconds. With
# no area, only the label shows. The windows are override-redirect, so the window manager leaves them alone and they
# never get keyboard focus. None is placed under the pointer: the app below would see the pointer leave and come back,
# and could show a tooltip in Claude's next screenshot.
FRAME = """
import sys, tkinter
label, x0, y0, x1, y1, width = sys.argv[1], *map(int, sys.argv[2:])
root = tkinter.Tk()
root.withdraw()
px, py = root.winfo_pointerxy()


def show(window, x, y, w, h):
    if x <= px < x + w and y <= py < y + h:
        return False
    window.overrideredirect(True)
    window.geometry(f"{w}x{h}+{x}+{y}")
    window.deiconify()
    return True


if x1 > x0:
    for x, y, w, h in ((x0, y0, x1 - x0, width), (x0, y1 - width, x1 - x0, width),
                       (x0, y0, width, y1 - y0), (x1 - width, y0, width, y1 - y0)):
        strip = tkinter.Toplevel(root, background="#e5484d")
        strip.withdraw()
        show(strip, x, y, w, h)
tag = tkinter.Toplevel(root)
tag.withdraw()
tkinter.Label(tag, text=label, background="#e5484d", foreground="white", font=("DejaVu Sans", -3 * width, "bold"),
              padx=width).pack()
tag.update_idletasks()
w, h = tag.winfo_reqwidth(), tag.winfo_reqheight()
x = min(max((x0 + x1 - w) // 2, 0), root.winfo_screenwidth() - w)
y = y0 + width if y1 - y0 > 3 * h else y1 + width  # inside the top of a large area, below a small one
if not show(tag, x, min(y, root.winfo_screenheight() - h), w, h):
    show(tag, x, max(y0 - h - width, 0), w, h)  # above the area instead
root.after(600, root.destroy)
root.mainloop()
"""
BADGE = (640, 620, 640, 620)  # where a label with no area goes: bottom middle, above the dock


# box: a small square around a point, kept on the screen
def box(coordinate):
    x, y = coordinate
    return max(x - 32, 0), max(y - 32, 0), min(x + 32, gui.WIDTH), min(y + 32, gui.HEIGHT)


# draw: run the frame program on the desktop and wait until it is gone. If the template has no Tk, nothing is drawn.
def draw(label, region):
    command = shlex.join(["python3", "-c", FRAME, label, *map(str, region), "8"])
    desktop.sandbox.commands.run(command + " || true")


# preview: with --step, move the pointer onto the point Claude chose and box it, so the room sees the target in the
# viewer before the action runs. Commands, typing, and key presses have no point, so they are only described.
def preview(name, args):
    action = f'run "{args.get("command")}"' if name == "bash" else name.replace("_", " ")
    if name in ("type", "key"):
        action += f' "{args["text"]}"'.replace("\n", "\\n")
    if "coordinate" in args:
        gui.move(args["coordinate"])
        draw("target", box(args["coordinate"]))
        action += f" at ({args['coordinate'][0]}, {args['coordinate'][1]}). The pointer is on the target"
    print(tagged("step", f"Claude wants to {action}"))


# flash: with --step, show the room what Claude just did. A screenshot or zoom frames the area captured, a click,
# scroll, or mouse move boxes the point, and typing or a key press shows the keys. It is drawn after the action and
# gone before this returns, so it is never in a screenshot Claude gets.
def flash(name, args):
    if name in ("screenshot", "zoom"):
        label, region = name, args["region"] if name == "zoom" else (0, 0, gui.WIDTH, gui.HEIGHT)
    elif name in gui.CLICKS or name in ("scroll", "mouse_move"):
        label = f"scroll {args['scroll_direction']}" if name == "scroll" else name.replace("_", " ")
        region = box(args["coordinate"]) if "coordinate" in args else BADGE
    elif name in ("type", "key"):
        text = args["text"].replace("\n", "\\n")
        label, region = f'{name} "{text if len(text) <= 40 else text[:40] + "..."}"', BADGE
    else:
        return
    draw(label, region)
