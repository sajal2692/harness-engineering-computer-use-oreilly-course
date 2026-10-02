"""The tools Claude can call, and run_tool, which runs one call and turns the outcome into a tool result.

Claude defines the tools' names and inputs. This demo's code is what runs them."""

import subprocess

import gui
import shell

# 1. The tool definitions Claude sees: Claude's bash tool, its text editor tool, and its computer use toolset.
#    Each is Anthropic-defined, so the entry names a version instead of a schema. Members this demo does not
#    implement are switched off.
TOOLS = [
    {"type": "bash_20250124", "name": "bash"},
    {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"},
    {"type": "computer_toolset_20260801",
     "configs": {member: {"enabled": False} for member in
                 ("left_click_drag", "left_mouse_down", "left_mouse_up", "middle_click", "hold_key", "cursor_position")}},
]


def image(picture):
    return [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": gui.as_png(picture)}}]


# 2. run_computer: one member of the computer use toolset. The member's name is the action.
def run_computer(name, args):
    if name == "screenshot":
        return image(gui.screenshot())
    if name == "zoom":
        return image(gui.zoom(args["region"]))
    if name in gui.BUTTONS:
        return gui.click(name, args.get("coordinate"), args.get("text"))
    if name == "type":
        return gui.type_text(args["text"])
    if name == "key":
        return gui.key(args["text"], args.get("repeat", 1))
    if name == "scroll":
        return gui.scroll(args["scroll_direction"], args["scroll_amount"], args.get("coordinate"), args.get("text"))
    if name == "mouse_move":
        return gui.mouse_move(args["coordinate"])
    if name == "wait":
        return gui.wait(args["duration"])
    raise ValueError(f"{name} is not implemented in this demo")


# 3. run_tool: run one tool call and return (content, is_error). Errors go back to Claude as text it can read.
def run_tool(call):
    try:
        if call.toolset_name == "computer":
            return run_computer(call.name, call.input), False
        if call.name == "bash":
            return shell.bash(call.input.get("command"), call.input.get("restart", False)), False
        if call.name == "str_replace_based_edit_tool":
            if call.input["command"] != "view":
                return "error: this demo's file tool can only view files. Use the text editor on screen.", True
            return shell.view(call.input["path"], call.input.get("view_range")), False
        return f"error: there is no tool called {call.name}", True
    except (ValueError, RuntimeError, KeyError) as error:
        return f"error: {error}", True
    except subprocess.TimeoutExpired:  # the input may still have reached the desktop
        return "timeout: no answer in 30 seconds. The action may have happened. Take a screenshot.", True
