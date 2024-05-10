
from tinychain.llm.ollama_chat_model import OllamaChatbotAI
from tinychain.prompt.prompts import ChatPromptTemplate
from tinychain.runnable.runnable_manager import RunableManager
llm = OllamaChatbotAI(model_name="llama2")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a world class technical documentation writer."),
    ("user", "{input}")
])

print(prompt)
exit(0)

chain = prompt | llm | llm

chain.invoke({})