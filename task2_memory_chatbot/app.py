"""
app.py - the Streamlit web page (what the user sees).

Run with:  streamlit run app.py

Streamlit re-runs this whole file every time the user clicks or types,
so anything we must remember between clicks is kept in st.session_state.
"""

import uuid

import streamlit as st

import chatbot
import memory_store
import preferences

st.set_page_config(page_title="Memory Chatbot", page_icon="🧠")
st.title("🧠 Chatbot with Memory")


def start_new_conversation():
    """Clear the screen and give the chat a new id. Long-term memory is NOT cleared."""
    st.session_state.conversation_id = str(uuid.uuid4())
    st.session_state.messages = []


# First time the page loads -> start a conversation
if "conversation_id" not in st.session_state:
    start_new_conversation()

# ---------- Sidebar: shows what the bot remembers ----------
with st.sidebar:
    st.header("Memory")
    if st.button("➕ New conversation"):
        start_new_conversation()
        st.rerun()

    st.metric("Q&As stored in vector DB", memory_store.count_all())

    st.subheader("Learned preferences")
    st.json(preferences.load_preferences())

    if st.button("🔄 Learn preferences now"):
        preferences.learn_preferences(memory_store.get_recent_questions(limit=10))
        st.rerun()

# ---------- Main area: the chat ----------
# Show the messages of the current conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Wait for the user to type something
question = st.chat_input("Ask me anything...")
if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = chatbot.get_answer(
                st.session_state.conversation_id,
                st.session_state.messages,
                question,
            )
        st.write(result["answer"])

    # Remember this turn for the rest of the conversation
    st.session_state.messages.append({"role": "user", "content": question})
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})

    if result["preferences_updated"]:
        st.toast("I learned something new about your preferences!")
        st.rerun()   # refresh so the sidebar shows the new preferences
