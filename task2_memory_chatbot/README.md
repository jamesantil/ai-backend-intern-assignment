# Task 2 – Streamlit chatbot that remembers you

A small RAG chatbot that learns from earlier conversations. Tell it what you like once, start a new chat later, and it already knows.

How it meets the brief:

- **Every question and answer is saved in a vector database** (ChromaDB), so past conversations can be searched by meaning.
- **Every 5 questions it learns your preferences**: likes, dislikes and other facts about you. It extracts them with the LLM and saves them.
- **New conversations start with that knowledge.** The saved preferences and the most relevant past Q&As go into the bot's instructions before every answer.

Everything runs locally: no API key, no cloud, no cost.

## Demo

Demo video: link coming soon.

The video shows:
1. **The bot learns about you.** After 5 messages it learns your likes, dislikes and facts, shown in the sidebar.
2. **A new conversation uses that memory.** The chat starts empty, and a movie or dinner suggestion follows your preferences without being told.
3. **You change your mind.** Say "I hate horror movies now", and horror moves from likes to dislikes. It never appears in both.

## How it works

```
You type a question in the Streamlit page (app.py)
        │
        ▼
chatbot.py
  1. load your saved preferences ............ preferences.py → data/preferences.json
  2. find the 3 most similar past Q&As ...... memory_store.py → ChromaDB      (Retrieve, dated)
  3. put both into the system prompt ........ chatbot.py                     (Augment)
  4. ask the model .......................... llm.py → Ollama (llama3.1:8b)  (Generate)
  5. save this Q&A .......................... memory_store.py
  6. every 5th Q&A: re-learn preferences .... preferences.py (LLM reads each message, Python merges)
        │
        ▼
Answer shown in the chat; sidebar shows what the bot has learned
```

"New conversation" only clears the screen. Long-term memory (the vector DB and the preferences file) is kept on disk, and that's the whole point.

## Files

| File | What it does |
|------|--------------|
| `app.py` | The Streamlit page: chat, a "New conversation" button, and a sidebar that shows the memory || `chatbot.py` | Puts it all together for each question (preferences + RAG search + LLM + saving + learning) |
| `memory_store.py` | ChromaDB: save every Q&A, search for similar ones, fetch recent user messages |
| `preferences.py` | Asks the LLM to pull likes/dislikes/facts out of your messages; Python merges them (no duplicates, newest wins) and saves them |
| `llm.py` | The only file that talks to the model, so switching LLMs means editing one file |
| `config.py` | All settings in one place (model, data folder, how often to learn) |
| `check_setup.py` | A quick self-test: is Ollama running, can the model return JSON, does vector search work |

## How to run

1. Install **Ollama** from https://ollama.com/download and leave it running.
2. Download the model (about 4.9 GB, one time):
   ```bash
   ollama pull llama3.1:8b
   ```
3. Set up Python 3.10+:
   ```bash
   cd task2_memory_chatbot
   python -m venv .venv
   .venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Run the self-test. You should see three PASS lines:
   ```bash
   python check_setup.py
   ```
5. Start the app and open http://localhost:8501:
   ```bash
   streamlit run app.py
   ```

To try it yourself: tell it 5 things about you, watch the sidebar fill in, click **New conversation**, then ask for a recommendation.
To wipe its memory, stop the app and delete the `data/` folder.

## Why these tools

| Tool | Why I picked it | What else I considered |
|------|-----------------|------------------------|
| **Streamlit** | The brief asks for it, and it has chat widgets built in, so the whole UI is under 80 lines of Python. | Gradio, Chainlit |
| **ChromaDB** | A real vector database that needs no server: `pip install`, it saves to a folder and has a built-in embedding model (all-MiniLM-L6-v2). | FAISS (no storage/metadata), Pinecone (cloud + key), Qdrant/pgvector (need a server) |
| **Ollama + Llama 3.1 8B** | Free, private, runs offline, and Ollama has a JSON mode that makes preference extraction reliable. I tried `codellama:13b` first; it's tuned for code and gave flatter answers. | OpenAI/Claude APIs (need a paid key), LM Studio |
| **JSON file for preferences** | It's one small summary that's always loaded in full, never searched. A readable file is easier to inspect than another database. | A second Chroma collection, SQLite |

## Things I had to fix along the way

- **The bot's own suggestions were saved as my likes.** The learner originally read the whole chat, so movies *the bot* recommended ended up under "likes". Now it only learns from what the user writes.
- **It once recommended a book when asked for a movie.** I added an "answer exactly what is asked" rule to the prompt.
- **Replies kept steering back to movies**, and it reacted oddly when told a new fact. The prompt now says to use memories only when relevant and to simply acknowledge new facts.
- **Changing your mind.** If you once said you love horror and later say you hate it, both Q&As stay in the vector DB. So now:
  - every memory the bot sees is dated and sorted oldest → newest, and the prompt says the newest information wins;
  - the learner moves the item from likes to dislikes;
  - the merge is done in plain Python (`merge_preferences`), so nothing ever ends up in both lists.
- **"Learn preferences now" duplicated items.** Re-learning the same messages added "horror genre" three times, because the LLM was rewriting the whole list each time. Now the LLM only extracts what the messages say, and Python merges it: duplicates are skipped ("rom-com" = "rom com series"), and a new dislike removes the old like. Clicking the button twice now gives the same result.
- **"I'll never watch rom-coms again" didn't move rom-com to dislikes.** Given a whole batch of messages at once, the 8B model missed that a later message overrode an earlier "I'd like to watch a rom-com". Now the learner reads one message at a time, oldest first, with the previous few as context for words like "it", and Python applies each result in order, so the latest message always wins. Hating "rom-com" also removes related likes such as "rom-com anime". The bot is also told never to argue with a stated dislike.
- **The learner sometimes invented preferences** (e.g. "sci-fi" the user never mentioned). Preference extraction now runs at temperature 0, and every new item must come from the user's own words.
- **Memory location depended on where you started the app.** The data folder is now always inside the project (or wherever `CHATBOT_DATA_DIR` points).

## Assumptions and limits

- **One user, no login.** For multiple users I'd tag every Q&A with a `user_id` and keep one preferences record per user.
- **Learning interval.** Preferences are learned every 5 questions, counted across conversations. This is configurable in `config.py`; the brief allows 5 to 10.
- **Model quality.** An 8B local model is good, not perfect: occasionally it phrases things oddly or over-uses a preference. Because only `llm.py` talks to the model, a stronger hosted model is a one-file change.
- **Answer delivery.** Answers appear in one go. Streaming them word by word would be a nice next step.
