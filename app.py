import streamlit as st
import time
from openai import OpenAI
import re
import io
import pandas as pd
import requests

# Set your OpenAI API key and assistant ID here
api_key = st.secrets["openai_apikey"]
assistant_id = st.secrets["assistant_id"]

# Set OpenAI client , assistant ai and assistant ai thread
@st.cache_resource
def load_openai_client_and_assistant():
    client = OpenAI(api_key=api_key)
    my_assistant = client.beta.assistants.retrieve(assistant_id)
    thread = client.beta.threads.create()

    return client, my_assistant, thread

client, my_assistant, assistant_thread = load_openai_client_and_assistant()

# Check in loop if assistant AI processes our request
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# Initiate assistant AI response
def get_assistant_response(user_input=""):
    message = client.beta.threads.messages.create(
        thread_id=assistant_thread.id,
        role="user",
        content=user_input,
    )

    run = client.beta.threads.runs.create(
        thread_id=assistant_thread.id,
        assistant_id=assistant_id,
    )

    run = wait_on_run(run, assistant_thread)

    # Retrieve all the messages added after our last user message
    messages = client.beta.threads.messages.list(
        thread_id=assistant_thread.id, order="asc", after=message.id
    )

    return messages.data[0].content[0].text.value, messages.data[0].file_ids

# Retrieve file content from OpenAI storage
def retrieve_file_content(file_id, api_key):
    url = f"https://api.openai.com/v1/files/{file_id}/content"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.content
    else:
        st.error("Failed to retrieve the file.")
        return None

if 'user_input' not in st.session_state:
    st.session_state.user_input = ''

def submit():
    st.session_state.user_input = st.session_state.query
    st.session_state.query = ''

st.title("Asistente Gerencia Gestion de Activos 🔧")

st.text_input("Puedo ayudarte en algo hoy?", key='query', on_change=submit)

user_input = st.session_state.user_input

st.write("You entered: ", user_input)

if user_input:
    result, file_ids = get_assistant_response(user_input)
    st.header('Assistant 🛠️', divider='rainbow')

    if file_ids:
        file_id = file_ids[0]  # Usamos el primer file_id que retorna el asistente
        st.write(f"File ID found: {file_id}")

        # Retrieve the file content
        file_content = retrieve_file_content(file_id, api_key)
        if file_content:
            # Create a file-like object and read it into a DataFrame
            file_like_object = io.BytesIO(file_content)
            df = pd.read_csv(file_like_object)
            st.write(df)  # Muestra el DataFrame en Streamlit

            st.download_button(
                label="Download File",
                data=file_content,
                file_name="downloaded_file.csv",  # Ajusta el nombre y extensión según sea necesario
                mime="text/csv"  # Ajusta el MIME type basado en el tipo de archivo
            )
    else:
        st.write("No file generated or returned by the assistant.")
