
from tinychain.llm.ollama_chat_model import OllamaChatbotAI
llm = OllamaChatbotAI(model_name="llama2")
rsp = llm.invoke("how can langsmith help with testing?")


