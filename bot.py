"""Slack bot: mention it in a channel and it answers from that channel's history."""
import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import config
from rag import answer, build_llm, build_vectorstore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("slack-rag-assistant")

app = App(token=config.required("SLACK_BOT_TOKEN"))
vectorstore = build_vectorstore()
llm = build_llm()
bot_user_id = app.client.auth_test()["user_id"]


@app.event("app_mention")
def handle_mention(event, say):
    thread_ts = event.get("thread_ts") or event["ts"]
    query = event.get("text", "").replace(f"<@{bot_user_id}>", "").strip()
    if not query:
        say("Ask me a question after the mention.", thread_ts=thread_ts)
        return
    try:
        say(answer(vectorstore, llm, query, event["channel"]), thread_ts=thread_ts)
    except Exception:
        # Message text is not logged: channel history can hold customer details.
        logger.exception("Failed to answer a mention in channel %s", event["channel"])
        say("Something went wrong while answering. Please try again.", thread_ts=thread_ts)


if __name__ == "__main__":
    SocketModeHandler(app, config.required("SLACK_APP_TOKEN")).start()
