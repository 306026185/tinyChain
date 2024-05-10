
from openai import OpenAI
import instructor

class ChatOllamaAI:

    def __init__(self,model_name) -> None:
        
        self.client = instructor.patch(
            OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
            )
        )
        self.model_name = model_name

    def bind_tools(self,tools):
        pass

    def invoke(self,messages):
        rsp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages
        )
        return rsp
    
    