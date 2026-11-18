# AI Backend Intern Assignment

Voice companion, WhatsApp and memory RAG. This repo has both parts of the assignment.

| | What | Where |
|---|---|---|
| **Task 1** | Architecture design doc (2 pages, one diagram per system): a voice AI companion for 100k users, and an LLM backend on WhatsApp | [`task1_architecture/Architecture_Design_Doc.pdf`](task1_architecture/Architecture_Design_Doc.pdf) |
| **Task 2** | A Streamlit RAG chatbot that saves every Q&A in a vector DB, learns your preferences every 5 questions and uses them in new conversations | [`task2_memory_chatbot/`](task2_memory_chatbot/) |
| **Demo** | A video walkthrough: the bot learns preferences, uses them in a new conversation, and handles a change of mind | [▶ Watch the demo video](https://drive.google.com/file/d/11nAaxObgZ5ezL5nCMwHSgUSugIm_sTM_/view?usp=sharing) |

## How the two tasks fit together

Both Task 1 systems need the same "brain": an LLM that remembers the user and uses that memory when it answers. Task 2 is a small, working version of that brain.

| In Task 2 (runs on a laptop) | In the Task 1 designs (100k users) |
|---|---|
| Streamlit page | Mobile voice app / WhatsApp |
| `chatbot.get_answer()` | A shared "Core AI service" behind FastAPI |
| ChromaDB in a local folder | Postgres + pgvector, with every row tagged by `user_id` |
| `preferences.json` | A user-profile table, cached in Redis |
| Learning preferences every 5 questions | A background job off the request path |
| Ollama (llama3.1:8b) via `llm.py` | A hosted LLM with a fallback provider, still behind one swappable module |

## Quick start (Task 2)

You need Python 3.10+ and [Ollama](https://ollama.com/download).

```bash
ollama pull llama3.1:8b
cd task2_memory_chatbot
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py             # should print PASS three times
streamlit run app.py              # opens http://localhost:8501
```

The full explanation (how it works, the tools I chose and why, assumptions, and what I fixed along the way) is in the [Task 2 README](task2_memory_chatbot/README.md).

## Repo layout

```
.
├── README.md                          ← you are here
├── task1_architecture/
│   └── Architecture_Design_Doc.pdf    ← Task 1 design doc
└── task2_memory_chatbot/
    ├── app.py                         ← Streamlit UI
    ├── chatbot.py                     ← RAG + memory logic
    ├── memory_store.py                ← ChromaDB (vector DB)
    ├── preferences.py                 ← learns likes / dislikes
    ├── llm.py                         ← the only file that talks to the LLM
    ├── config.py                      ← settings
    ├── check_setup.py                 ← self-test
    ├── requirements.txt
    ├── .env.example
    └── README.md
```
