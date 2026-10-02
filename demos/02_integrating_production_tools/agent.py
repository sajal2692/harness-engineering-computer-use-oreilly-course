"""The Claude agent loop: send the conversation, run every tool call in the reply in order, and send back the results."""

import json
import sys

import anthropic

import record
from output import tagged
from tools import TOOLS, run_tool
from utils import preview

MODEL = "claude-sonnet-5-5"
SKIPPED = "Not executed: an earlier computer action in this turn failed."


def run(task, system, step=False):
    # 1. With step on, wait for Enter at each hand-off in the loop
    def pause(message):
        if step:
            input(tagged("step", message) + " ")

    # 2. Send the conversation to Claude. The SDK retries rate limits, overloads, and dropped connections.
    client = anthropic.Anthropic(max_retries=5)
    messages = [{"role": "user", "content": task}]
    record.start(task)
    pause("Press Enter to send the task to Claude.")
    for turn in range(1, 31):
        try:
            response = client.messages.create(
                model=MODEL, max_tokens=16000, system=system, tools=TOOLS, messages=messages,
                thinking={"type": "adaptive", "display": "summarized"},  # return a summary of Claude's reasoning
                output_config={"effort": "medium"},
                cache_control={"type": "ephemeral"},  # reuse the unchanged start of the conversation
            )
        except anthropic.AuthenticationError:
            sys.exit("[error] The API key was rejected. Check ANTHROPIC_API_KEY in .env.")
        except anthropic.APIError as error:
            sys.exit(f"[error] The Claude API call failed: {error}")

        # 3. Show what Claude read, thought, and said, and keep its reply in the conversation
        usage = response.usage
        cached = usage.cache_read_input_tokens or 0
        total = usage.input_tokens + cached + (usage.cache_creation_input_tokens or 0)
        print(f"\n{'─' * 36} turn {turn} {'─' * 36}")
        tokens = f"read {total:,} input tokens ({cached:,} from cache) and wrote {usage.output_tokens:,}"
        print(tagged("claude", tokens))
        notes = []
        for block in response.content:
            if block.type == "thinking" and block.thinking:
                print(tagged("thinking", block.thinking))
                notes.append(block.thinking)
            elif block.type == "text":
                print(tagged("claude", block.text))
                notes.append(block.text)
        record.turn(turn, f"Claude {tokens}.", notes)
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            if response.stop_reason != "end_turn":
                print(tagged("stopped", f"Claude stopped early: {response.stop_reason}"))
            return

        # 4. Run every tool call in the reply, in order. After a failure, skip the rest but still answer each one.
        results, failed = [], False
        calls = [block for block in response.content if block.type == "tool_use"]
        for call in calls:
            print(tagged("claude", f"calls {call.name} {json.dumps(call.input)}"))
            if failed:
                content, is_error = SKIPPED, True
            else:
                if step:
                    preview(call.name, call.input)  # show the room what Claude is about to do
                pause("Press Enter to run it on the desktop.")
                content, is_error = run_tool(call)
                failed = is_error and call.toolset_name == "computer"
            shown = content if isinstance(content, str) else "an image"
            print(tagged("result", ("error " if is_error else "") + shown))
            record.call(call.name, call.input, content, is_error)
            result = {"type": "tool_result", "tool_use_id": call.id, "content": content, "is_error": is_error}
            if call.toolset_name:
                result["toolset_name"] = call.toolset_name  # every computer result must name its toolset
            results.append(result)
        pause("Press Enter to send the results to Claude.")
        messages.append({"role": "user", "content": results})
    print(tagged("stopped", "The run reached its limit of 30 turns without an answer."))
