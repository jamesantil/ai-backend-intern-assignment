"""
memory_store.py - the vector database (ChromaDB).

Job 1: SAVE every question + answer.
Job 2: SEARCH for past Q&As that are similar to a new question (this is the "R" in RAG).

How a vector DB works, in one sentence:
each text is turned into a list of numbers (an "embedding") that captures its meaning,
so texts with similar meaning end up close together and can be found by similarity.
ChromaDB does the embedding for us with a small free model that runs locally.
"""

import uuid
from datetime import datetime

import chromadb
from config import CHROMA_DIR, NUM_MEMORIES_TO_RECALL

# PersistentClient saves to disk, so memories survive app restarts
_db = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _db.get_or_create_collection(name="chat_history")


def save_qa(conversation_id: str, question: str, answer: str) -> None:
    """Store one question/answer pair in the vector database."""
    _collection.add(
        ids=[str(uuid.uuid4())],
        documents=[f"User: {question}\nBot: {answer}"],   # this text gets embedded
        metadatas=[{
            "conversation_id": conversation_id,
            "question": question,
            "answer": answer,
            "time": datetime.now().isoformat(),
        }],
    )


def search_similar(question: str, k: int = NUM_MEMORIES_TO_RECALL) -> list[str]:
    """
    Return up to k past Q&As whose meaning is closest to the new question.

    Each one starts with the date it was said, e.g. "[2026-11-17 16:46] User: ...",
    and they are sorted oldest -> newest. People change their minds, so the bot
    needs to know which memory is newer when two of them disagree.
    """
    if _collection.count() == 0:
        return []
    results = _collection.query(
        query_texts=[question],
        n_results=min(k, _collection.count()),
        include=["documents", "metadatas"],
    )
    found = list(zip(results["documents"][0], results["metadatas"][0]))
    found.sort(key=lambda pair: pair[1]["time"])          # oldest first, newest last

    dated = []
    for document, metadata in found:
        date = metadata["time"][:16].replace("T", " ")    # "2026-11-17T16:46:08.5" -> "2026-11-17 16:46"
        dated.append(f"[{date}] {document}")
    return dated


def get_recent_questions(limit: int = 10) -> list[str]:
    """
    Return the user's most recent messages (used to learn preferences).
    We use only what the USER said - not the bot's answers - so things the bot
    suggested are not mistaken for things the user likes.
    """
    data = _collection.get(include=["metadatas"])
    metadatas = sorted(data["metadatas"], key=lambda m: m["time"])   # oldest -> newest
    return [m["question"] for m in metadatas[-limit:]]


def count_all() -> int:
    """How many Q&As are stored in total."""
    return _collection.count()
