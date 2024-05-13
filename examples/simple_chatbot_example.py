
import time
import ollama

import pandas as pd
import numpy as np

import streamlit as st

st.set_page_config(page_title="🤗💬 chat with ollama")

with st.sidebar:
    st.title('🤗💬 chat with ollama')
    model_name = st.selectbox(
        "可以从下列模型选择一个模型",
        ("llama3", "mistral", "gemma"))

    st.write("选择了:", model_name)
   

def generate_response(prompt_input):
    response = ollama.chat(model=model_name, messages=[
        {
            'role': 'user',
            'content': prompt_input,
        },
    ])
    return response['message']['content']

if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "I am very help assistant "}]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write((message["content"]))

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt) 
            st.write(response) 
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)