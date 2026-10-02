# Demo 1: Building Computer Tools

Claude gets a bash session, a file viewer, and screenshot, click, and type tools on a Linux desktop that runs in
Docker on your machine. Every tool is built here from plain programs: `docker exec` and `bash` for the shell,
ImageMagick's `import` for screenshots, and `xdotool` for mouse and keyboard input. The script prints each command
it runs.

The task uses both the shell and the GUI:

> Count the receipt files in ~/receipts with a command. Then open the text editor, type a one-line note with the
> count, and save it as ~/notes/receipt_count.txt. Finally, read the saved file with the file tool to check it.

```text
main.py ──> agent.py ──> Claude                    the model chooses the next tool calls
               │
               └──> tools.py ──> shell.py ──> docker exec ──> bash session ──┐
                         │                                                    ├──> the Docker desktop
                         └─────> gui.py ───> docker exec ──> import, xdotool ─┘
```

## Setup

Do the repository setup in the top-level README first. Docker Desktop must be running. Everything below runs from
this directory. The first run builds the desktop image, which takes a few minutes.

## Files

| File | What it does |
|---|---|
| `main.py` | The task and the system prompt |
| `Dockerfile`, `start.sh`, `xfce/` | The desktop: Debian with Xfce on a 2560 x 1440 virtual display, drawn at twice the size, with a file manager, terminal, Firefox, the Mousepad text editor, and image and PDF viewers |
| `desktop.py` | Starts and removes the container, and runs programs inside it |
| `shell.py` | The bash session and the file viewer |
| `gui.py` | Screenshots, coordinate scaling, and mouse and keyboard input |
| `tools.py` | The tool definitions Claude sees, and `run_tool`, which runs one call |
| `agent.py` | The agent loop |
| `record.py` | The run record: `runs/<date-time>/trail.md`, with each turn's tool calls, results, and the screenshots Claude received |
| `utils.py` | The `--step` preview: it moves the pointer onto Claude's target before a click. Not a tool |
| `output.py` | The colored `[tag]` at the start of every printed line |

## Running it

```bash
uv run main.py --step
```

Open the viewer link it prints in your browser. `--step` pauses at each hand-off in the loop: before the task goes
to Claude, before each tool call runs, and before the results go back. Before a click runs, the pointer moves onto
the point Claude chose, so the viewer shows the target. Press Enter to continue.

```bash
uv run main.py
```

Without `--step`, it waits once for Enter so you can open the viewer, then runs straight through. Either way, when
Claude finishes the desktop stays up until you press Enter, so you can look at what it left on screen. Ctrl-C
removes it at any point.

## The run record

Every run writes `runs/<date-time>/trail.md`. It lists each turn: the tokens Claude read, what it said, each tool
call with its input, and what came back. Screenshots are saved next to it as the exact images Claude received, so a
Markdown preview shows the run as Claude saw it.

## What this harness leaves out

These gaps are on purpose. It does not check what a command may do before running it, limit the network, check that
a click landed on what Claude meant or that the intended window has focus before typing, ask a person before an
effect, or trim old screenshots from the conversation. The file tool can only view files, and long command output is
cut rather than saved.

## Troubleshooting

- **`[error] Docker is not running`:** start Docker Desktop.
- **Port 6080 is in use:** stop whatever uses it, or a container left from an earlier run with
  `docker rm -f computer-use-demo1`.
- **The viewer shows a black screen:** reload the page; the desktop can take a moment after the first build.
