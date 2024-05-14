from tinychain.llm.ollama_chat_model import OllamaChatbotAI


if __name__ == "__main__":
    ollama_chat_model = OllamaChatbotAI()
    ollama_chat_model.invoke([
        ("system","you are very help email assistant"),
        ("human","you write query price of the Sony notebook"),
        ("assitant","you know the all brand of notebook"),
    ])

    