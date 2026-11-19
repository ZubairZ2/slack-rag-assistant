# slack-rag-assistant

A Slack bot that answers questions from a channel's own history. Mention it with a question and it replies in the thread with a summary, the details, and links to the past threads it used.

It was built for a customer-success team whose answers to recurring questions were buried in years of channel history.

## How it works

1. **Export.** `export_channel.py` downloads a channel's messages and thread replies to a JSON Lines file, waiting out Slack's rate limits.
2. **Index.** `index_history.py` embeds each message with a local Ollama model and stores it in Pinecone with its thread timestamp.
3. **Answer.** `bot.py` listens for mentions in Socket Mode. For each question it retrieves the closest messages, groups them by thread, and asks the chat model to answer from that context only.

The bot says so when the history does not contain an answer. Every answer carries links to the source threads, so the reader can check it.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in the values
ollama pull mxbai-embed-large
```

You need a Slack app with Socket Mode on, the `app_mentions:read`, `channels:history` and `chat:write` scopes, and a Pinecone index whose dimension matches the embedding model (1024 for `mxbai-embed-large`).

## Run

```bash
mkdir -p data
python export_channel.py      # writes data/channel_history.jsonl
python index_history.py       # embeds and stores it
python bot.py                 # starts the bot
```

`python ask.py` asks questions from the terminal without Slack.

## Notes

- Secrets are read from the environment. Nothing is hard-coded.
- Message text is not written to logs, because channel history can hold customer details.
- Embeddings run locally through Ollama, so channel content is only sent out at answer time, as the retrieved context for the chat model.

## Stack

Python, Slack Bolt, LangChain, Pinecone, Ollama, OpenAI.
