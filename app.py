import streamlit as st
import time
import base64
from openai import OpenAI

# Set your OpenAI API key and assistant ID here
api_key = st.secrets["openai_apikey"]
assistant_id = st.secrets["assistant_id"]

# Set openAi client , assistant ai and assistant ai thread
@st.cache_resource
def load_openai_client_and_assistant():
    client = OpenAI(api_key=api_key)
    my_assistant = client.beta.assistants.retrieve(assistant_id)
    thread = client.beta.threads.create()

    return client, my_assistant, thread

client, my_assistant, assistant_thread = load_openai_client_and_assistant()

# check in loop  if assistant ai parse our request
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# initiate assistant ai response
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

    response = messages.data[0].content[0]
    
    # Verificar si la respuesta es una imagen o texto
    if hasattr(response, 'image_data'):
        return {
            'type': 'image',
            'content': response.image_data,  # Asegúrate de usar el campo correcto aquí
        }
    elif hasattr(response, 'csv_data'):
        return {
            'type': 'csv',
            'content': response.csv_data,  # Asegúrate de usar el campo correcto aquí
        }
    else:
        return {
            'type': 'text',
            'content': response.text.value,
        }

def generate_download_link(data, filename, filetype):
    b64 = base64.b64encode(data).decode()  # Codificar los datos en base64
    href = f'<a href="data:file/{filetype};base64,{b64}" download="{filename}">Descargar {filename}</a>'
    return href

if 'user_input' not in st.session_state:
    st.session_state.user_input = ''

def submit():
    st.session_state.user_input = st.session_state.query
    st.session_state.query = ''


st.title(" Asistente Gerencia Gestion de Activos 🔧")

st.text_input("Puedo ayudarte en algo hoy?", key='query', on_change=submit)

user_input = st.session_state.user_input

st.write("You entered: ", user_input)

if user_input:
    result = get_assistant_response(user_input)
    st.header('Asistente :blue[Mantenimiento] 🛠️', divider='rainbow')

    if result['type'] == 'text':
        st.text(result['content'])
    elif result['type'] == 'image':
        # Decodificar la imagen desde base64
        image_data = base64.b64decode(result['content'])
        st.image(image_data, use_column_width=True)
        
        # Crear un enlace de descarga
        st.markdown(generate_download_link(image_data, "grafico.jpg", "jpg"), unsafe_allow_html=True)
    
    elif result['type'] == 'csv':
        # Decodificar el CSV desde base64
        csv_data = base64.b64decode(result['content'])
        
        # Crear un enlace de descarga
        st.markdown(generate_download_link(csv_data, "detalle_equipos.csv", "csv"), unsafe_allow_html=True)
