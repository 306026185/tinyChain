from typing import Union,Any,List,Dict
from dataclasses import dataclass


@dataclass
class BaseMessage:
    content:str
    def __init__(self,content:Union[str, List[Union[str, Dict]]], **kwargs: Any):
        self.content = content

class SystemMessage(BaseMessage):
    role:str
    def __init__(self,content:str) -> None:
        self.role = "system"
        self.content = content


class HumanMessage(BaseMessage):
    def __init__(self,content:str) -> None:
        self.role = "user"
        self.content = content

    def to_dict(self)->str:
        return {
            "role":"user",
            "content":self.content
        }

class AIMessage(BaseMessage):
    def __init__(self,content:str)->None:
        self.role = "assistant"
        self.content = content

class ChatMessage(BaseMessage):
    def __init__(self,content:str,role:str) -> None:
        self.role = role
        self.content = content

class ChatMessage(BaseMessage):
    pass

base_message_map:Dict[str,BaseMessage] = {
    "human":HumanMessage,
    "user":HumanMessage,
    "ai":AIMessage,
    "system":SystemMessage
}



if __name__ == "__main__":
    pass