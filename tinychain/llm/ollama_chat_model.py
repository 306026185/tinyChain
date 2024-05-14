from typing import Union,List,Tuple

import ollama

from tinychain.message.messages import HumanMessage,BaseMessage
from tinychain.runnable.runnable_manager import Runnable


PromptType = Union[str, List[Union[Tuple[str, str], BaseMessage]]]

class OllamaChatbotAI(Runnable):
    def __init__(self,model_name:str="llama3") -> None:
        super().__init__()
        self.model_name = model_name

    def invoke(self,prompt_str:PromptType):

        messages = []

        if isinstance(input, str):
            human_message = HumanMessage(content=prompt_str)
            messages.append(human_message.to_dict())
        elif isinstance(input, list):
            if all(isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) and isinstance(item[1], str) for item in input):
                return 'List[Tuple[str, str]]'
            elif all(isinstance(item, BaseMessage) for item in input):
                for message in input:
                    messages.append(message.to_dict())
            
        print(messages)  
        # rsp = ollama.chat(model='llama3', messages=messages)

        # return rsp['message']['content']