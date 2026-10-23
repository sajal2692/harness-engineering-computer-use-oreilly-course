# Harness Engineering for Computer Use

Companion repository for my O'Reilly live course **Harness Engineering for Computer Use**.

This repository holds the code for the course's two demos. I run both live in class, so you don't need to install
anything to follow along. To run them yourself afterwards, use the setup below.

## Repository map

```text
demos/01_building_computer_tools/        Demo 1: shell and GUI tools built from bash, ImageMagick, and xdotool on a Docker desktop
demos/02_integrating_production_tools/   Demo 2: posting vendor bills in GnuCash on an E2B Desktop sandbox, with routing and controls
tests/                                   Checks that call each demo's tools directly, with no model
pyproject.toml                           Pinned Python dependencies
.env.example                             Template for the Anthropic and E2B API keys
```

Each demo directory has its own README with setup, how to run it, and troubleshooting.

## Requirements

- macOS or Linux, Python 3.12 or newer, and [uv](https://docs.astral.sh/uv/)
- Docker Desktop, running, for Demo 1
- An Anthropic API key. The demos use Claude Sonnet 5.5
- An [E2B](https://e2b.dev) API key for Demo 2. The free plan is enough; each run uses a few cents of credit.
  Build Demo 2's template once with `uv run template.py` in its folder

## Setup

From this directory:

```bash
uv sync
cp .env.example .env
```

Add your Anthropic and E2B API keys to `.env`.

## Tests

```bash
uv run python tests/run_demo_1.py
uv run python tests/run_demo_2.py
```

Each script starts its demo's desktop, calls its tools directly, the way a model would, and checks the output. Each
runs for about a minute and calls no model. Demo 2's check creates one E2B desktop.

## Computer use on macOS or Windows

Both demos run Linux desktops, but the harness doesn't depend on the operating system. The agent loop and the tool
definitions stay the same; only the code that touches the machine changes. In Demo 1 that is `gui.py`, for
screenshots and input, and `desktop.py`, for starting the machine.

- **macOS:** capture the screen with `screencapture` or ScreenCaptureKit, and send mouse and keyboard input with
  Quartz events (CGEvent). The program running the agent needs Screen Recording and Accessibility permission in
  System Settings. On a Retina display, screenshot pixels and screen points differ, so keep a scaling step like
  `to_display()` in Demo 1.
- **Windows:** send mouse and keyboard input with `SendInput`, and read controls by name with UI Automation. A
  normal process can't send input to an app running as administrator, so run the agent with ordinary rights.
  Display scaling makes the same coordinate step necessary.
- **Containment:** give the agent its own machine, not your desktop with your email, browser sessions, and files.
  Lume runs macOS virtual machines on Apple silicon, Windows Sandbox gives a throwaway Windows desktop, and Cua is an
  open-source framework built around such virtual machines.

As of October 2026, products that do this include computer use in the Claude desktop app on macOS and Windows
(research preview), OpenAI's Codex app on macOS, and the Agent Workspace preview in Windows.
