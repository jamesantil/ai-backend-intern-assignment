"""
llm.py - the ONLY file that talks to the AI model.

We use Ollama, which runs an open-source LLM (Llama 3.1 8B) on your own
computer. No API key, no internet needed after the model is downloaded.

Every other file calls ask_llm(...) and gets back plain text.
To switch to another LLM later (OpenAI, Claude, ...) you only change this file.
"""

import ollama
from config import MODEL_NAME, OLLAMA_HOST

# Connects to the Ollama app running in the background on your PC
client = ollama.Client(host=OLLAMA_HOST)


def ask_llm(system_prompt: str, messages: list[dict], json_mode: bool = False) -> str:
    """
    Send a conversation to the local LLM and return its text reply.

    system_prompt: instructions for the bot (who it is, what it knows about the user)
    messages:      list like [{"role": "user", "content": "Hi"}, {"role": "assistant", ...}]
    json_mode:     True = force the model to reply with valid JSON (used for preferences).
                   It also sets temperature to 0: no creativity, so the model sticks to
                   what the user actually wrote instead of inventing extra preferences.
    """
    # Ollama takes the system prompt as the first message in the list
    all_messages = [{"role": "system", "content": system_prompt}] + messages

    response = client.chat(
        model=MODEL_NAME,
        messages=all_messages,
        format="json" if json_mode else None,
        options={"temperature": 0} if json_mode else None,
    )
    return response["message"]["content"]
