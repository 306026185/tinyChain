from typing import Any,Protocol
from abc import ABC

class Runnable(Protocol):
    def invoke(self,input,input_schema="json"):
        """invoke interface"""

class Node:
    def __init__(self,next:Runnable=None) -> None:
        self.next=None


class RunableManager:

    def __init__(self) -> None:
        self.head = None

    def add(self,other:Runnable):
        newNode = None(other)
        if(self.head):
            current = self.head
            while(current.next):
                current = current.next
        else:
            self.head = other

    def invoke(self,prompt:Any):
        current = self.head
        while(current):
            prompt = current.invoke(prompt)
            current = current.next


  


