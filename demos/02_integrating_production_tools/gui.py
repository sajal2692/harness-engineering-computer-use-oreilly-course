"""The GUI tools on E2B: each action is one call to the E2B Desktop SDK, which runs xdotool inside the sandbox.

The desktop is the same size as Claude's screenshots, so coordinates need no scaling here."""

import base64
import io
import math
import time

from PIL import Image

import desktop
from output import tagged

WIDTH, HEIGHT = desktop.RESOLUTION
CLICKS = {"left_click": "left_click", "right_click": "right_click", "double_click": "double_click"}


def visual_tokens(width, height):  # how Claude's current models count an image
    return math.ceil(width / 28) * math.ceil(height / 28)


def as_png(image):
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue()).decode()


# 1. screenshot: E2B returns the screen as PNG bytes
def screenshot():
    image = Image.open(io.BytesIO(desktop.sandbox.screenshot()))
    print(tagged("screen", f"captured {image.width} x {image.height} ({visual_tokens(*image.size):,} visual tokens)"))
    return image


# 2. on_screen: refuse a point that is not on the screen, so no input is sent
def on_screen(coordinate):
    x, y = coordinate
    if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        raise ValueError(f"out of bounds: ({x}, {y}) is outside the {WIDTH} x {HEIGHT} screen. No input was sent.")
    return x, y


# 3. click, type_text, key, scroll, and wait: one SDK call each
def click(name, coordinate=None):
    point = on_screen(coordinate) if coordinate else ()
    getattr(desktop.sandbox, CLICKS[name])(*point)
    return "OK"


def type_text(text):
    desktop.sandbox.write(text)
    return "OK"


def key(text, repeat=1):
    # The SDK maps lowercase names like ctrl and enter to xdotool's. It lowercases everything else, and xdotool does
    # not know "return", so Claude's "Return" needs its alias. A gap like this is why the next check is a screenshot.
    keys = [{"return": "enter"}.get(name.lower(), name) for name in text.split("+")]
    for _ in range(repeat):
        desktop.sandbox.press(keys)
    return "OK"


def scroll(scroll_direction, scroll_amount, coordinate=None):
    if coordinate:
        desktop.sandbox.move_mouse(*on_screen(coordinate))
    desktop.sandbox.scroll(scroll_direction, scroll_amount)
    return "OK"


def mouse_move(coordinate):
    desktop.sandbox.move_mouse(*on_screen(coordinate))
    return "OK"


def wait(duration):
    time.sleep(min(duration, 10))
    return "OK"


# 4. zoom: crop a region of the screen and enlarge it, so small text is easier to read
def zoom(region):
    on_screen(region[:2]), on_screen((region[2] - 1, region[3] - 1))
    crop = screenshot().crop(region)
    crop.thumbnail((WIDTH, HEIGHT))
    if crop.width < WIDTH and crop.height < HEIGHT:
        scale = min(WIDTH / crop.width, HEIGHT / crop.height)
        crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.LANCZOS)
    return crop
