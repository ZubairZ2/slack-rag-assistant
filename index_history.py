"""Embed an exported channel history and store it in Pinecone.

Usage: python index_history.py [input_path]
"""
import json
import sys

from langchain_core.documents import Document

from rag import build_vectorstore

BATCH_SIZE = 100


def load_documents(path: str):
    with open(path, encoding="utf-8") as lines:
        for line in lines:
            message = json.loads(line)
            text = (message.get("text") or "").strip()
            if not text or message.get("subtype"):
                continue  # skip joins, bot notices and empty messages
            yield Document(
                page_content=text,
                metadata={
                    "ts": message["ts"],
                    "thread_ts": message.get("thread_ts", message["ts"]),
                    "user": message.get("user", ""),
                },
            )


def index(path: str) -> int:
    vectorstore = build_vectorstore()
    batch, total = [], 0
    for document in load_documents(path):
        batch.append(document)
        if len(batch) == BATCH_SIZE:
            vectorstore.add_documents(batch, ids=[d.metadata["ts"] for d in batch])
            total += len(batch)
            batch = []
    if batch:
        vectorstore.add_documents(batch, ids=[d.metadata["ts"] for d in batch])
        total += len(batch)
    return total


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/channel_history.jsonl"
    print(f"Indexed {index(path)} messages from {path}")
