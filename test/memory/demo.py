from tinychain.memory.chat_message_history import ChatMessageHistory
from tinychain.prompt.chat_prompt import ChatPromptTemplate
from tinychain.llm.ollama_chat_model import OllamaChatbotAI

from tinychain.runnable.runnable_manager import RunableManager
from tinychain.output_parser import OutputParser


# creat chain

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Answer all questions to the best of your ability.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)


input1 = "Translate this sentence from English to French: I love programming."
demo_ephemeral_chat_history = ChatMessageHistory()
demo_ephemeral_chat_history.add_user_message(input1)

chain 

response = chain.invoke(
    {
        "messages": demo_ephemeral_chat_history.messages,
    }
)

demo_ephemeral_chat_history.add_ai_message(response)

input2 = "What did I just ask you?"

demo_ephemeral_chat_history.add_user_message(input2)

chain.invoke(
    {
        "messages": demo_ephemeral_chat_history.messages,
    }
)