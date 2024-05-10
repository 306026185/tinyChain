from typing import Union,Any,List,Dict
from dataclasses import dataclass

class BaseMessage:

    def __init__(self,content:Union[str, List[Union[str, Dict]]], **kwargs: Any):
        self.content = content

class SystemMessage(BaseMessage):
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



if __name__ == "__main__":
    pass