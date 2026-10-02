"""The GUI tools: take screenshots of the virtual display, and send it mouse and keyboard input with xdotool."""

import base64
import io
import math
import time

from PIL import Image

import desktop
from output import tagged

DISPLAY = (2560, 1440)  # the desktop's real size, set in the Dockerfile
SCREENSHOT = (1280, 720)  # what the model sees; its coordinates are in this space
SCALE = DISPLAY[0] / SCREENSHOT[0]
BUTTONS = {"left_click": (1, 1), "right_click": (3, 1), "double_click": (1, 2), "triple_click": (1, 3)}
SCROLL_BUTTONS = {"up": 4, "down": 5, "left": 6, "right": 7}  # X11 sends wheel movement as button clicks


def visual_tokens(width, height):  # how Claude's current models count an image
    return math.ceil(width / 28) * math.ceil(height / 28)


# 1. capture: take a full-size screenshot inside the desktop with ImageMagick's import
def capture():
    png = desktop.run(["import", "-window", "root", "png:-"], binary=True).stdout
    return Image.open(io.BytesIO(png))


def as_png(image):
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue()).decode()


# 2. screenshot: capture the display, then scale it down to the model's size
def screenshot():
    full = capture()
    small = full.resize(SCREENSHOT, Image.LANCZOS)
    print(tagged("screen", f"captured {full.width} x {full.height} ({visual_tokens(*full.size):,} visual tokens at full "
                           f"size). The model gets {SCREENSHOT[0]} x {SCREENSHOT[1]} "
                           f"({visual_tokens(*SCREENSHOT):,} visual tokens)."))
    return small


# 3. to_display: check a point from the model is on its screenshot, then scale it to the real display
def to_display(coordinate):
    x, y = coordinate
    if not (0 <= x < SCREENSHOT[0] and 0 <= y < SCREENSHOT[1]):
        raise ValueError(f"out of bounds: ({x}, {y}) is outside the {SCREENSHOT[0]} x {SCREENSHOT[1]} screenshot. "
                         "No input was sent.")
    point = round(x * SCALE), round(y * SCALE)
    print(tagged("scale", f"({x}, {y}) on the screenshot is {point} on the display"))
    return point


def xdotool(*args):
    result = desktop.run(["xdotool", *map(str, args)])
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "xdotool failed")


# 4. click: move the pointer, hold any modifier keys, press and release the button
def click(name, coordinate=None, text=None):
    button, count = BUTTONS[name]
    if coordinate:
        xdotool("mousemove", "--sync", *to_display(coordinate))
    modifiers = text.split("+") if text else []
    if modifiers:
        xdotool("keydown", *modifiers)
    xdotool("click", "--repeat", count, "--delay", 100, button)
    if modifiers:
        xdotool("keyup", *modifiers)
    return "OK"


# 5. type_text and key: send text or key presses to whichever window has keyboard focus
def type_text(text):
    xdotool("type", "--delay", 20, "--", text)
    return "OK"


def key(text, repeat=1):
    xdotool("key", "--repeat", repeat, "--", *text.split())
    return "OK"


# 6. scroll, mouse_move, and wait
def scroll(scroll_direction, scroll_amount, coordinate=None, text=None):
    if coordinate:
        xdotool("mousemove", "--sync", *to_display(coordinate))
    xdotool("click", "--repeat", scroll_amount, SCROLL_BUTTONS[scroll_direction])
    return "OK"


def mouse_move(coordinate):
    xdotool("mousemove", "--sync", *to_display(coordinate))
    return "OK"


def wait(duration):
    time.sleep(min(duration, 10))
    return "OK"


# 7. zoom: crop a region of a full-size screenshot, so small text stays sharp, and fit it to the model's size
def zoom(region):
    x0, y0, x1, y1 = region
    to_display((x0, y0)), to_display((x1 - 1, y1 - 1))  # both corners must be on the screenshot
    crop = capture().crop([round(value * SCALE) for value in region])
    crop.thumbnail(SCREENSHOT, Image.LANCZOS)
    print(tagged("screen", f"zoomed into {region}; the model gets {crop.width} x {crop.height} at full detail"))
    return crop
