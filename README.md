# Harness Engineering for Computer Use

Companion repository for the O'Reilly live course **Harness Engineering for Computer Use**, taught by Sajal Sharma.

The course has instructor-led demos. You can follow them in class without installing anything. This repository lets
you read the code during the session and run the demos yourself afterwards.

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
