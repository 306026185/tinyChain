from tinychain.prompt.chat_prompt import ChatPromptTemplate
from tinychain.llm.ollama_chat_model import OllamaChatbotAI

from tinychain.runnable.runnable_manager import RunableManager
from tinychain.output_parser import OutputParser

# prompt -> query llm -> response

# get Chat
prompt = ChatPromptTemplate.from_template("tell me a joke about {topic}")

runable_manager = RunableManager()
runable_manager.head = prompt
model = OllamaChatbotAI()
model.next = OutputParser()
prompt.next = model

runable_manager.invoke({"topic": "bears"})
print(runable_manager.context)
