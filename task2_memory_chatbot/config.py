"""
config.py - all settings in ONE place.

If you want to change the model, the folder where data is saved,
or how often preferences are learned, you only change it here.
"""

import os
from dotenv import load_dotenv

# Read the .env file (optional) so you can override settings without editing code
load_dotenv()

# --- LLM settings (local model through Ollama) ---
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.1:8b")                   # downloaded with: ollama pull llama3.1:8b
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")        # where the Ollama app listens

# --- Storage settings ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
# Everything is saved inside this folder. Set CHATBOT_DATA_DIR to keep a separate memory (e.g. for a demo).
DATA_DIR = os.getenv("CHATBOT_DATA_DIR", os.path.join(PROJECT_DIR, "data"))
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")       # vector database files
PREFERENCES_FILE = os.path.join(DATA_DIR, "preferences.json")  # learned user preferences

# --- Memory settings ---
LEARN_EVERY_N_QUESTIONS = 5   # after every 5 questions we learn preferences (assignment says 5 to 10)
NUM_MEMORIES_TO_RECALL = 3    # how many similar past Q&As we pull from the vector DB per question

# Make sure the data folder exists
os.makedirs(DATA_DIR, exist_ok=True)
