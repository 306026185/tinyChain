from tinychain.prompt.chat_prompt import ChatPromptTemplate
from tinychain.llm.ollama_chat_model import OllamaChatbotAI

from tinychain.runnable.runnable_manager import RunableManager


prompt = ChatPromptTemplate.from_template("tell me a joke about {topic}")

runable_manager = RunableManager()
runable_manager.head = prompt
prompt.next = OllamaChatbotAI()
runable_manager.invoke({"topic": "bears"})
print(runable_manager.context)
