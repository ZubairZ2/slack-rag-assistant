"""Ask questions from the terminal, without Slack. Useful for checking retrieval.

Usage: python ask.py
"""
import config
from rag import answer, build_llm, build_vectorstore


def main():
    vectorstore, llm = build_vectorstore(), build_llm()
    channel_id = config.required("SLACK_CHANNEL_ID")
    print("Ask a question, or type 'exit'.")
    while True:
        query = input("> ").strip()
        if query.lower() == "exit":
            return
        if query:
            print(answer(vectorstore, llm, query, channel_id))


if __name__ == "__main__":
    main()
