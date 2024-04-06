import streamlit as st
import g4f
from g4f.client import Client
import sqlite3
import google.generativeai as genai
# import pyttsx3
import pyperclip
import requests
from PIL import Image
import io


API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": "Bearer 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"}

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")

# Create a connection to the database
conn = sqlite3.connect('chat_history.db')
c = conn.cursor()

# Create table if not exists
try:
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (conversation_id INTEGER, role TEXT, content TEXT)''')
    conn.commit()
except Exception as e:
    st.error(f"An error occurred: {e}")

def generate_image_from_model(prompt):
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    image_bytes = response.content
    image = Image.open(io.BytesIO(image_bytes))
    return image


# Streamlit app
def main():
    try:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        if "conversation_id" not in st.session_state:
            st.session_state.conversation_id = 1

        models = {
            "🚀 Airoboros 70B": "airoboros-70b",
            "🔮 Gemini Pro": "gemini-pro",
            "📷 StabilityAI": "stabilityai/stable-diffusion-xl-base-1.0",
            "🧨 GPT-3-turbo": g4f.models.default
        }

        columns = st.columns(3)  # Split the layout into three columns
        with columns[0]:
            st.header("DarkGPT")

        with columns[2]:
            selected_model_display_name = st.selectbox("Select Model", list(models.keys()), index=0)

        with columns[1]:
            selected_model = models[selected_model_display_name]

        # Sidebar (left side) - New chat button
        if st.sidebar.button("✨ New Chat", key="new_chat_button"):
            st.session_state.chat_history.clear()
            st.session_state.conversation_id += 1

        # Sidebar (left side) - Display saved chat
        st.sidebar.write("Chat History")
        c.execute("SELECT DISTINCT conversation_id FROM chat_history")
        conversations = c.fetchall()
        for conv_id in reversed(conversations):
            c.execute("SELECT content FROM chat_history WHERE conversation_id=? AND role='bot' LIMIT 1",
                      (conv_id[0],))
            first_bot_response = c.fetchone()
            if first_bot_response:
                if st.sidebar.button(" ".join(first_bot_response[0].split()[0:5])):
                    display_conversation(conv_id[0])

        # Sidebar (left side) - Clear Chat History button
        if st.sidebar.button("Clear Chat History ✖️"):
            st.session_state.chat_history.clear()
            c.execute("DELETE FROM chat_history")
            conn.commit()

        # Main content area (center)
        st.markdown("---")

        user_input = st.chat_input("Ask Anything ...")

        if user_input:
            if selected_model == "gemini-pro":
                try:
                    GOOGLE_API_KEY = "AIzaSyC8_gwU5LSVQJk3iIXyj5xJ94ArNK11dXU"
                    genai.configure(api_key=GOOGLE_API_KEY)
                    model = genai.GenerativeModel('gemini-pro')
                    prompt = user_input
                    response = model.generate_content(prompt)
                    bot_response = response.candidates[0].content.parts[0].text

                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.chat_history.append({"role": "bot", "content": bot_response})

                    # Store chat in the database
                    for chat in st.session_state.chat_history:
                        c.execute("INSERT INTO chat_history VALUES (?, ?, ?)",
                                  (st.session_state.conversation_id, chat["role"], chat["content"]))
                    conn.commit()

                    for index, chat in enumerate(st.session_state.chat_history):
                        with st.chat_message(chat["role"]):
                            if chat["role"] == "user":
                                st.markdown(chat["content"])
                            elif chat["role"] == "bot":
                                st.markdown(chat["content"])




                except Exception as e:
                    st.error(f"An error occurred: {e}")

            elif selected_model == "stabilityai/stable-diffusion-xl-base-1.0":
                prompt = user_input
                generated_image = generate_image_from_model(prompt)
                st.image(generated_image, caption="Generated Image", width=400)

            elif selected_model == "GPT-3-turbo":
                try:

                    client = Client()
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": user_input}],
                        model=g4f.models.default,
                    )

                    # Extract the GPT response and print it
                    bot_response = response.choices[0].message.content

                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.chat_history.append({"role": "bot", "content": bot_response})

                    for index, chat in enumerate(st.session_state.chat_history):
                        with st.chat_message(chat["role"]):
                            if chat["role"] == "user":
                                st.markdown(chat["content"])
                            elif chat["role"] == "bot":
                                st.markdown(chat["content"])


                except Exception as e:
                    st.error(f"An error occurred: {e}")

            else:
                try:
                    client = Client()
                    response = client.chat.completions.create(
                        model=models[selected_model_display_name],
                        messages=[{"role": "user", "content": user_input}],
                    )
                    bot_response = response.choices[0].message.content

                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.chat_history.append({"role": "bot", "content": bot_response})

                    # Store chat in the database
                    for chat in st.session_state.chat_history:
                        c.execute("INSERT INTO chat_history VALUES (?, ?, ?)",
                                  (st.session_state.conversation_id, chat["role"], chat["content"]))
                    conn.commit()

                    # Display chat history
                    for index, chat in enumerate(st.session_state.chat_history):
                        with st.chat_message(chat["role"]):
                            if chat["role"] == "user":
                                st.markdown(chat["content"])
                            elif chat["role"] == "bot":
                                st.markdown(chat["content"])


                except Exception as e:
                    st.error(f"An error occurred: {e}")



    except Exception as e:
        st.error(f"An error occurred: {e}")


def display_conversation(conversation_id):
    c.execute("SELECT * FROM chat_history WHERE conversation_id=?", (conversation_id,))
    chats = c.fetchall()
    st.markdown(f"### Conversation")
    for chat in chats:
        st.markdown(f"{chat[1]}")
        st.markdown(f"{chat[2]}")


if __name__ == "__main__":
    main()
