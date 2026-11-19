"""Retrieval and answer generation shared by the Slack bot and the CLI."""
from collections import defaultdict

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

import config

MAX_CONTEXT_CHARS = 8000
NOT_FOUND = "I am not able to find sufficient information to answer your query."

PROMPT = ChatPromptTemplate.from_template(
    """You are an assistant for a team Slack channel. Answer the question using only
the context below, which is made of past messages and threads from that channel.

CONTEXT FROM CHANNEL HISTORY:
{context}

QUESTION: {query}

Structure the answer as:
- Summary: a short overview of what you found
- Details: the specific solution, steps or information
- Source: the thread links from the context that support the answer
- Related: connected issues or follow-ups, if any

If the context does not contain the answer, say:
"I don't have enough information from our channel history to answer this."
"""
)


def build_vectorstore() -> PineconeVectorStore:
    index = Pinecone(api_key=config.required("PINECONE_API_KEY")).Index(config.PINECONE_INDEX_NAME)
    embeddings = OllamaEmbeddings(model=config.EMBEDDING_MODEL, base_url=config.OLLAMA_BASE_URL)
    return PineconeVectorStore(embedding=embeddings, index=index)


def build_llm() -> ChatOpenAI:
    return ChatOpenAI(model=config.CHAT_MODEL, api_key=config.required("OPENAI_API_KEY"))


def thread_link(channel_id: str, thread_ts: str) -> str:
    return f"https://{config.SLACK_WORKSPACE_URL}/archives/{channel_id}/p{thread_ts.replace('.', '')}"


def retrieve_context(vectorstore, query: str, channel_id: str, top_k: int = 10):
    """Return matching messages grouped by thread, each with a link to the thread."""
    docs = vectorstore.as_retriever(search_kwargs={"k": top_k}).invoke(query)
    threads = defaultdict(list)
    for doc in docs:
        thread_ts = doc.metadata.get("thread_ts")
        if thread_ts:
            threads[thread_ts].append(doc.page_content)
    if not threads:
        return None
    context = "\n\n".join(
        f"Thread {thread_link(channel_id, ts)}:\n" + "\n".join(messages)
        for ts, messages in threads.items()
    )
    return context[:MAX_CONTEXT_CHARS]


def answer(vectorstore, llm, query: str, channel_id: str) -> str:
    context = retrieve_context(vectorstore, query, channel_id)
    if not context:
        return NOT_FOUND
    return (PROMPT | llm).invoke({"query": query, "context": context}).content
