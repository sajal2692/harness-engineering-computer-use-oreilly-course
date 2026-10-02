"""The tools Claude can call, the harness checks around them, and run_tool, which runs one call.

Three controls live here: a route line for every call, a permission check on every command, and an approval before
anything is posted to the books."""

import re
import shlex

from e2b import TimeoutException

import desktop
import gui
import shell
from output import tagged

NETWORK = {"curl", "wget", "ssh", "scp", "sftp", "rsync", "nc", "ftp"}
WRITES = re.compile(r"(>|\b(sed\s+-i|tee|mv|rm|chmod|chown|truncate)\b)[^|;&]*finance/")  # a write aimed at finance/
BATCH = f"{desktop.HOME}/work/approved_batch.csv"
routes = []  # ("shell", "gui", or "batch", what was done), in order, for the summary at the end

# 1. The tool definitions Claude sees: the same three Anthropic-defined tools as Demo 1, plus submit_batch, a
#    custom tool for the decision that needs a person's approval.
TOOLS = [
    {"type": "bash_20250124", "name": "bash"},
    {"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"},
    {"type": "computer_toolset_20260801",
     "configs": {member: {"enabled": False} for member in ("left_click_drag", "left_mouse_down", "left_mouse_up",
                                                         "middle_click", "triple_click", "hold_key",
                                                         "cursor_position")}},
    {"name": "submit_batch", "description": "Submit your decision for every invoice as CSV text with the columns "
     "file,vendor,invoice_number,invoice_date,amount_cad,expense_account,decision,reason, where decision is post or "
     "hold. A person reviews it. If they approve, GnuCash opens with the company books so you can post the bills "
     "marked post.",
     "input_schema": {"type": "object", "properties": {"csv": {"type": "string"}}, "required": ["csv"]}},
]


# 2. permission: check a command before it runs. Refuse network programs, paths outside the home folder, writes to
#    the finance records, and anything that touches the books except a read-only query. This is a simple string
#    check; underneath it, the sandbox has no internet and the vendor list is read-only for the agent's account.
def permission(command):
    try:
        words = shlex.split(command)
    except ValueError:
        return "the command could not be parsed"
    if NETWORK & set(words):
        return f"{(NETWORK & set(words)).pop()} reaches the network, which this task does not need"
    for path in re.findall(r"(?<![\w.~])/[\w./-]+", command):  # absolute paths, not ~/ or folder/file
        if path != "/dev/null" and not path.startswith(desktop.HOME):
            return f"{path} is outside {desktop.HOME}"
    if WRITES.search(command):
        return "the finance records are read-only for this task"
    if "books/" in command and "sqlite3 -readonly" not in command:
        return "the books can only be read, with sqlite3 -readonly; bills are posted in GnuCash after approval"
    return None


# 3. submit: show the batch and, only if a person types y, save it and open the books. No answer counts as no.
def submit(csv):
    print(tagged("approval", f"Claude's decisions for this batch:\n{csv.strip()}"))
    try:
        answer = input(tagged("approval", "Approve this batch for posting? [y/N]") + " ")
    except EOFError:
        answer = ""
    if answer.strip().lower() != "y":
        return "denied: the person did not approve the batch. Nothing was posted, and the books stay closed.", True
    desktop.sandbox.files.write(BATCH, csv)
    desktop.open_books()
    return (f"approved and saved to {BATCH}. GnuCash is now open with the company books. Post each bill marked "
            "post, then check the books with sqlite3 -readonly."), False


def image(picture):
    return [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": gui.as_png(picture)}}]


# 4. run_computer: one member of the computer use toolset. The member's name is the action.
def run_computer(name, args):
    if name in ("screenshot", "zoom"):
        return image(gui.screenshot() if name == "screenshot" else gui.zoom(args["region"]))
    if name in gui.CLICKS:
        return gui.click(name, args.get("coordinate"))
    if name == "type":
        return gui.type_text(args["text"])
    if name == "key":
        return gui.key(args["text"], args.get("repeat", 1))
    if name == "scroll":
        return gui.scroll(args["scroll_direction"], args["scroll_amount"], args.get("coordinate"))
    if name == "mouse_move":
        return gui.mouse_move(args["coordinate"])
    if name == "wait":
        return gui.wait(args["duration"])
    raise ValueError(f"{name} is not implemented in this demo")


# 5. run_tool: print the route, check permission, run the call, and return (content, is_error)
def run_tool(call):
    route = "gui" if call.toolset_name == "computer" else "batch" if call.name == "submit_batch" else "shell"
    detail = call.input.get("command") or call.input.get("path") or call.name
    routes.append((route, detail))
    print(tagged("route", f"{route}: {detail}"))
    try:
        if call.toolset_name == "computer":
            return run_computer(call.name, call.input), False
        if call.name == "bash":
            refusal = permission(call.input.get("command", ""))
            if refusal:
                print(tagged("blocked", refusal))
                shell.write_log(f"\n$ {call.input.get('command')}\n[blocked by the permission check: {refusal}]\n")
                return f"blocked by the permission check: {refusal}. The command did not run.", True
            return shell.bash(call.input["command"]), False
        if call.name == "str_replace_based_edit_tool":
            if call.input["command"] != "view":
                return "error: this demo's file tool can only view files.", True
            return shell.view(call.input["path"], call.input.get("view_range")), False
        if call.name == "submit_batch":
            return submit(call.input["csv"])
        return f"error: there is no tool called {call.name}", True
    except (ValueError, RuntimeError, KeyError) as error:
        return f"error: {error}", True
    except TimeoutException:  # the input may still have reached the desktop
        return "timeout: no answer in 30 seconds. The action may have happened. Take a screenshot.", True
