import streamlit as st
from g4f.client import Client
import sqlite3
import google.generativeai as genai
from diffusers import DiffusionPipeline
import matplotlib.pyplot as plt
import torch


# import pyttsx3
# import pyperclip

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


def generate_image(pipe, prompt, params):
    img = pipe(prompt, **params).images

    num_images = len(img)
    if num_images > 1:
        fig, ax = plt.subplots(nrows=1, ncols=num_images)
        for i in range(num_images):
            ax[i].imshow(img[i]);
            ax[i].axis('off');

    else:
        fig = plt.figure()
        plt.imshow(img[0]);
        plt.axis('off');
    plt.tight_layout()


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
            "📷 StabilityAI": "stabilityai/stable-diffusion-xl-base-1.0"

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
                    GOOGLE_API_KEY = "Gemini"
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
                pipe = DiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0",
                                                         torch_dtype=torch.float32, use_safetensors=True,
                                                         variant="fp16")
                pipe.to("cpu")

                params = {'num_inference_steps': 100, 'num_images_per_prompt': 2}
                generate_image(pipe, user_input, params)

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
