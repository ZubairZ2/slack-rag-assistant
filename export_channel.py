"""Export a Slack channel, including thread replies, to a JSON Lines file.

Usage: python export_channel.py [output_path]
"""
import json
import sys
import time

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import config

PAGE_SIZE = 200
PAUSE_SECONDS = 1.5  # stays under Slack's rate limits for history calls


def call_with_retry(method, **kwargs):
    """Call a Slack API method, waiting out rate limits."""
    while True:
        try:
            return method(**kwargs)
        except SlackApiError as error:
            if error.response.status_code != 429:
                raise
            wait = int(error.response.headers.get("Retry-After", 30))
            print(f"Rate limited. Waiting {wait}s.")
            time.sleep(wait)


def paginate(method, **kwargs):
    cursor = None
    while True:
        response = call_with_retry(method, cursor=cursor, limit=PAGE_SIZE, **kwargs)
        yield from response["messages"]
        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            return
        time.sleep(PAUSE_SECONDS)


def export(channel_id: str, output_path: str) -> int:
    client = WebClient(token=config.required("SLACK_BOT_TOKEN"))
    count = 0
    with open(output_path, "w", encoding="utf-8") as out:
        for message in paginate(client.conversations_history, channel=channel_id):
            out.write(json.dumps(message) + "\n")
            count += 1
            is_thread_parent = message.get("thread_ts") == message.get("ts")
            if not is_thread_parent:
                continue
            replies = paginate(client.conversations_replies, channel=channel_id, ts=message["ts"])
            for reply in replies:
                if reply["ts"] == message["ts"]:
                    continue  # the parent is returned again as the first reply
                out.write(json.dumps(reply) + "\n")
                count += 1
    return count


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/channel_history.jsonl"
    total = export(config.required("SLACK_CHANNEL_ID"), path)
    print(f"Saved {total} messages to {path}")
