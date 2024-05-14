from typing import List
from dataclasses import dataclass

from tinychain.message.messages import BaseMessage,AIMessage,HumanMessage,SystemMessage

class ChatMessageHistory:

    def __init__(self) -> None:
        self.messages:List[BaseMessage] = []

    def add_user_message(self,prompt):
        self.messages.append(HumanMessage(content=prompt))

    def add_ai_message(self,prompt):
        self.messages.append(AIMessage(content=prompt))
