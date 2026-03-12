import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/search"

st.set_page_config(page_title="Book Assistant", layout="centered")

st.title("📚 Book Assistant")
st.caption("Ask questions about books from books.toscrape.com")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message.get("images"):
            cols = st.columns(len(message["images"]))
            for col, img in zip(cols, message["images"]):
                col.image(f"{BASE_URL}{img}")

        if message.get("tables"):
            for table in message["tables"]:
                st.markdown(table, unsafe_allow_html=True)


# Chat input
user_query = st.chat_input("Ask about a book...")

if user_query:

    st.session_state.messages.append({
        "role": "user",
        "content": user_query
    })

    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Searching..."):

            try:
                response = requests.post(
                    API_URL,
                    json={"query": user_query},
                    timeout=180
                )

                data = response.json()

                answer = data.get("answer", "")
                images = data.get("images", [])
                tables = data.get("tables", [])

                st.markdown(answer)

                if images:
                    cols = st.columns(len(images))
                    for col, img in zip(cols, images):
                        col.image(f"{BASE_URL}{img}")

                if tables:
                    for table in tables:
                        st.markdown(table, unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "images": images,
                    "tables": tables
                })

            except Exception as e:
                st.error(str(e))