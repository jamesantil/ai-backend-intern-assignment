"""
check_setup.py - run this BEFORE the app to confirm everything works.

    python check_setup.py

It tests the 3 building blocks one by one and prints PASS / FAIL for each:
  1. The local LLM (Ollama) answers
  2. The LLM can return valid JSON (needed to learn preferences)
  3. The vector database can save and search
It does NOT touch your real chat memory in the data/ folder.
"""

import json

import chromadb

from config import MODEL_NAME, OLLAMA_HOST
from llm import ask_llm


def check_llm():
    print(f"1. Asking the local model '{MODEL_NAME}' at {OLLAMA_HOST} ...")
    reply = ask_llm("You are a test bot.", [{"role": "user", "content": "Reply with just the word OK."}])
    print(f"   Model replied: {reply.strip()[:60]}")


def check_json():
    print("2. Checking the model can return JSON ...")
    reply = ask_llm(
        'Reply ONLY with JSON like {"likes": [...], "dislikes": [...]}.',
        [{"role": "user", "content": "I love sci-fi movies and I hate horror."}],
        json_mode=True,
    )
    data = json.loads(reply)   # raises an error if it is not valid JSON
    print(f"   Parsed JSON: {data}")


def check_vector_db():
    print("3. Checking the vector database (first run downloads a small embedding model) ...")
    db = chromadb.EphemeralClient()                       # in-memory, nothing saved to disk
    col = db.get_or_create_collection("setup_test")
    col.add(ids=["1", "2"], documents=["I love space movies like Interstellar", "My favourite food is pizza"])
    found = col.query(query_texts=["recommend a sci-fi film"], n_results=1)["documents"][0][0]
    print(f"   Search for 'sci-fi film' found: '{found}'")
    assert "Interstellar" in found, "search returned the wrong memory"


if __name__ == "__main__":
    all_ok = True
    for check in (check_llm, check_json, check_vector_db):
        try:
            check()
            print("   PASS\n")
        except Exception as error:
            all_ok = False
            print(f"   FAIL: {error}\n")

    if all_ok:
        print("All checks passed. Start the app with:  streamlit run app.py")
    else:
        print("Some checks failed. Is the Ollama app running, and did you run 'ollama pull "
              f"{MODEL_NAME}'?")
