import streamlit as st
import requests
import io
import pandas as pd

# Simulating OpenAI client setup
from openai import OpenAI

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

# Function to get response from thread
def get_response(thread):
    return client.beta.threads.messages.list(thread_id=thread.id)

# Function to extract file_ids from the thread
def get_file_ids_from_thread(thread):
    response = get_response(thread)
    file_ids = [
        file_id
        for m in response.data
        for file_id in m.file_ids
    ]
    return file_ids

# Function to write file to a temporary directory
def write_file_to_temp_dir(file_id, output_path):
    url = f"https://api.openai.com/v1/files/{file_id}/content"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        with open(output_path, "wb") as file:
            file.write(response.content)
        return output_path
    else:
        st.error("Failed to retrieve the file from OpenAI.")
        return None

# Function to process file and prepare for download
def process_file_and_prepare_download(thread):
    file_ids = get_file_ids_from_thread(thread)
    if file_ids:
        some_file_id = file_ids[0]  # Use the first file_id found in the thread
        output_path = "/tmp/some_data.csv"  # Temporary path to save the file
        saved_file_path = write_file_to_temp_dir(some_file_id, output_path)
        
        if saved_file_path:
            with open(saved_file_path, "rb") as file:
                st.download_button(
                    label="Download CSV",
                    data=file,
                    file_name="some_data.csv",
                    mime="text/csv"
                )
        else:
            st.error("Error saving the file.")
    else:
        st.write("No file_id found in the thread.")

# Example usage in Streamlit
st.title("Asistente Gerencia Gestion de Activos 🔧")

user_input = st.text_input("Puedo ayudarte en algo hoy?")

if user_input:
    # Simulate assistant processing and saving a file (in reality, this will be your assistant's logic)
    # For this example, assume the assistant has already processed the data and created a thread with a file

    # Use the process_file_and_prepare_download function to handle the file download
    process_file_and_prepare_download(assistant_thread)
