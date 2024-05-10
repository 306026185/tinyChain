import ollama
from tinychain.message.messages import HumanMessage
from tinychain.runnable.runnable_manager import Runnable,RunableManager

class OllamaChatbotAI(Runnable,RunableManager):
    def __init__(self,model_name:str="llama3") -> None:
        self.model_name = model_name

    def invoke(self,prompt_str:str):

        messages = []
        if type(prompt_str) is str:
            human_message = HumanMessage(content=prompt_str)
            messages.append(human_message.to_dict())
        rsp = ollama.chat(model='llama3', messages=messages)

        return rsp['message']['content']