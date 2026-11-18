"""
preferences.py - learn and remember what the user likes / dislikes.

Every few questions we send the recent chat to the LLM and ask:
"What does this user like and dislike?"
The answer is merged with what we already knew and saved to a JSON file,
so a brand-new conversation can start with this knowledge.

Example of the saved file (data/preferences.json):
{
  "likes": ["slow sci-fi movies like Interstellar", "nature documentaries"],
  "dislikes": ["horror movies"],
  "other_facts": ["lives in Delhi"]
}
"""

import json
import os

from config import PREFERENCES_FILE
from llm import ask_llm

EMPTY_PREFERENCES = {"likes": [], "dislikes": [], "other_facts": []}


def load_preferences() -> dict:
    """Read saved preferences from disk (or return empty ones)."""
    if not os.path.exists(PREFERENCES_FILE):
        return dict(EMPTY_PREFERENCES)
    with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_preferences(prefs: dict) -> None:
    """Write preferences to disk."""
    with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2, ensure_ascii=False)


def learn_preferences(recent_questions: list[str]) -> dict:
    """
    Read the user's recent messages, find their preferences, and merge them
    into what we already knew. Returns the updated preferences (and saves them).

    The work is split in two:
      - the LLM reads ONE message at a time and says what it states
        (a small model is reliable at this; asked to sort out a whole batch
        it sometimes missed that a later message changed an earlier one)
      - plain Python merges each result in order, oldest -> newest, so a later
        message always overrides an earlier one, nothing is duplicated, and
        learning the same messages twice gives the same result
    """
    prefs = load_preferences()
    for i, message in enumerate(recent_questions):
        earlier = recent_questions[max(0, i - 3):i]   # a little context, for words like "it" / "this genre"
        found = extract_from_message(message, earlier, prefs)
        prefs = merge_preferences(prefs, found)
    save_preferences(prefs)
    return prefs


def extract_from_message(message: str, earlier: list[str], prefs: dict) -> dict:
    """Ask the LLM which likes / dislikes / facts this ONE user message states."""
    known_items = prefs["likes"] + prefs["dislikes"] + prefs["other_facts"]
    system_prompt = (
        "You extract a user's personal preferences from ONE message the user wrote. "
        "Reply with ONLY a JSON object with exactly these keys: "
        '"likes", "dislikes", "other_facts" - each a list of short strings. '
        "Only include what THIS message clearly says about the user "
        "(e.g. 'I love sci-fi' -> likes: 'sci-fi movies'; "
        "'I will never watch horror again' -> dislikes: 'horror movies'). "
        "Only lasting likes, dislikes and facts count. Questions and one-off requests are NOT preferences, "
        "even if they mention a topic (e.g. 'suggest me a party game', 'recommend a book', "
        "'which genre am I talking about') - return empty lists for them. "
        "If the message says 'it' or 'this', use the earlier messages to work out what it refers to. "
        "If an item is the same thing as one of the already-known items, use exactly the same wording. "
        "Do not invent anything."
    )
    user_message = (
        f"Already-known items (for wording only): {json.dumps(known_items)}\n"
        f"Earlier messages (only for context): {json.dumps(earlier)}\n\n"
        f"The message to read: {message}"
    )
    reply = ask_llm(system_prompt, [{"role": "user", "content": user_message}], json_mode=True)
    try:
        return json.loads(reply)
    except json.JSONDecodeError:
        return {}   # bad JSON -> learn nothing from this message instead of crashing


FILLER_WORDS = {"genre", "genres", "series", "movies", "movie", "films", "film", "shows", "show", "the"}


def _key(text: str) -> str:
    """Simplify a preference for comparing: "Rom-Com movies" -> "rom com"."""
    words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
    words = [w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words if w not in FILLER_WORDS]
    return " ".join(words)


def same_item(a: str, b: str) -> bool:
    """
    True if two preference strings mean the same thing, e.g.
    "rom-com" = "Rom com series" = "rom-coms",  "horror" = "horror genre".
    We ignore case, punctuation, plural "s" and filler words like "genre".
    """
    return _key(a) == _key(b)


def is_about(like: str, dislike: str) -> bool:
    """True if a like is (or contains) something now disliked, e.g. "rom-com anime" is about "rom-com"."""
    return same_item(like, dislike) or f" {_key(dislike)} " in f" {_key(like)} "


def merge_preferences(old_prefs: dict, found: dict) -> dict:
    """
    Merge newly found preferences into the saved ones. The new ones always win:
      - a new like    -> removed from dislikes (if there), added to likes once
      - a new dislike -> removed from likes (if there), added to dislikes once
      - a new fact    -> added once
    So nothing is ever duplicated, and nothing can be in both likes and dislikes.
    """
    prefs = {key: list(old_prefs.get(key, [])) for key in EMPTY_PREFERENCES}

    def add(item, to_list):
        if not any(same_item(x, item) for x in to_list):
            to_list.append(item)

    for item in found.get("likes", []):
        prefs["dislikes"] = [x for x in prefs["dislikes"] if not same_item(x, item)]
        add(item, prefs["likes"])
    for item in found.get("dislikes", []):          # dislikes go last: if the model put something in both,
        # the safe "dislike" wins. Hating "rom-com" also drops a like for "rom-com anime".
        prefs["likes"] = [x for x in prefs["likes"] if not is_about(x, item)]
        add(item, prefs["dislikes"])
    for item in found.get("other_facts", []):
        add(item, prefs["other_facts"])

    # Also clean up duplicates that may already be in an old saved file
    for key in prefs:
        unique = []
        for item in prefs[key]:
            if not any(same_item(x, item) for x in unique):
                unique.append(item)
        prefs[key] = unique
    return prefs


def preferences_as_text(prefs: dict) -> str:
    """Turn the preferences dict into readable text for the bot's system prompt."""
    lines = []
    if prefs.get("likes"):
        lines.append("Likes: " + ", ".join(prefs["likes"]))
    if prefs.get("dislikes"):
        lines.append("Dislikes: " + ", ".join(prefs["dislikes"]))
    if prefs.get("other_facts"):
        lines.append("Other facts: " + ", ".join(prefs["other_facts"]))
    return "\n".join(lines) if lines else "Nothing known yet."
