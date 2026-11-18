"""
chatbot.py - the "brain". It connects all the pieces.

For every user question it does 5 steps:
  1. Load the user's saved preferences            (preferences.py)
  2. Search the vector DB for similar past Q&As   (memory_store.py)  <- RAG retrieval
  3. Build a system prompt with that knowledge and ask the LLM  (llm.py)
  4. Save the new question + answer in the vector DB
  5. Every N questions, learn/update preferences
"""

from config import LEARN_EVERY_N_QUESTIONS
from llm import ask_llm
import memory_store
import preferences


def build_system_prompt(prefs_text: str, memories: list[str]) -> str:
    """Create the instructions the LLM sees before the conversation."""
    memories_text = "\n---\n".join(memories) if memories else "None."
    return (
        "You are a friendly personal assistant with long-term memory.\n\n"
        f"What you know about this user from earlier conversations:\n{prefs_text}\n\n"
        f"Related snippets from past conversations (each starts with its date, oldest first):\n{memories_text}\n\n"
        "People change their minds. If any of this information disagrees, the NEWEST wins: "
        "a later snippet beats an earlier one, and what the user says in this conversation beats everything. "
        "Use this knowledge naturally to personalise your answers "
        "(for example, recommend things they like and avoid things they dislike) "
        "without the user having to repeat themselves. "
        "Only bring up what you remember when it is relevant to the current message; "
        "don't steer every reply back to the same topic. "
        "When the user tells you something new about themselves, simply acknowledge it in a friendly way. "
        "Take what they say about their own likes and dislikes at face value: never argue, doubt it, "
        "or try to talk them back into something they said they hate. "
        "Answer exactly what is asked: if they ask for a movie, suggest a real movie, not a book. "
        "Keep answers concise."
    )


def get_answer(conversation_id: str, chat_history: list[dict], question: str) -> dict:
    """
    Answer one question.

    conversation_id: id of the current chat session
    chat_history:    messages of THIS conversation so far
    question:        the new user question

    Returns a dict with the answer and whether preferences were just updated.
    """
    # 1. What do we already know about the user?
    prefs = preferences.load_preferences()
    prefs_text = preferences.preferences_as_text(prefs)

    # 2. RAG: find similar past Q&As
    memories = memory_store.search_similar(question)

    # 3. Ask the LLM
    system_prompt = build_system_prompt(prefs_text, memories)
    messages = chat_history + [{"role": "user", "content": question}]
    answer = ask_llm(system_prompt, messages)

    # 4. Save this Q&A
    memory_store.save_qa(conversation_id, question, answer)

    # 5. Every N questions, learn preferences from the recent chat
    learned = False
    if memory_store.count_all() % LEARN_EVERY_N_QUESTIONS == 0:
        recent = memory_store.get_recent_questions(limit=LEARN_EVERY_N_QUESTIONS)
        preferences.learn_preferences(recent)
        learned = True

    return {"answer": answer, "preferences_updated": learned}
