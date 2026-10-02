# Harness Engineering for Computer Use

Companion repository for the O'Reilly live course **Harness Engineering for Computer Use**, taught by Sajal Sharma.

The course has instructor-led demos. You can follow them in class without installing anything. This repository lets
you read the code during the session and run the demos yourself afterwards.

## Repository map

```text
demos/01_building_computer_tools/   Demo 1: shell and GUI tools built from bash, ImageMagick, and xdotool on a Docker desktop
tests/                              Checks that call each demo's tools directly, with no model
pyproject.toml                      Pinned Python dependencies
.env.example                        Template for the Anthropic API key
```

Each demo directory has its own README with setup, how to run it, and troubleshooting.

## Requirements

- macOS or Linux, Python 3.12 or newer, and [uv](https://docs.astral.sh/uv/)
- Docker Desktop, running
- An Anthropic API key. The demos use Claude Sonnet 5.5

## Setup

From this directory:

```bash
uv sync
cp .env.example .env
```

Add your Anthropic API key to `.env`.

## Tests

```bash
uv run python tests/run_demo_1.py
```

The script starts the demo's desktop, calls its tools directly, the way a model would, and checks the output. It
runs for about a minute and calls no model.
