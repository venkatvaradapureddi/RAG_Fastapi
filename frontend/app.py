import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/search"

st.set_page_config(page_title="Book Assistant", layout="wide")

st.title("📚 Book Assistant")
st.write("Ask questions about books scraped from books.toscrape.com")

# SESSION STATE (chat history)
if "messages" not in st.session_state:
    st.session_state.messages = []

# DISPLAY PAST MESSAGES
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("tables"):
            st.markdown("### 📋 Product Information")
            for table in message["tables"]:
                st.markdown(table, unsafe_allow_html=True)

        # if message.get("images"):
        #     cols = st.columns(len(message["images"]))
        #     for col, img in zip(cols, message["images"]):
        #         with col:
        #             st.image(img)


user_query = st.chat_input("Ask a question about a book...")

if user_query:

    # Add user message to chat
    st.session_state.messages.append(
        {"role": "user", "content": user_query}
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    # Assistant response
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

                if tables:
                    st.markdown("### 📋 Product Information")
                    for table in tables:
                        st.markdown(table, unsafe_allow_html=True)

                # if images:
                #     cols = st.columns(len(images))
                #     for col, img in zip(cols, images):
                #         with col:
                #             st.image(img)

                # Save assistant response to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "tables": tables,
                    "images": images
                })

            except Exception as e:
                st.error(f"Error: {str(e)}")