from typing import Any,Protocol
from abc import ABC,abstractmethod

class Runnable(ABC):
    def __init__(self) -> None:
        self.next = None

    @abstractmethod
    def invoke(self,input,input_schema="json"):
        """invoke interface"""

        
# linked list
class RunableManager:

    def __init__(self) -> None:
        self.head:Runnable = None
        self.context = None

    def add(self,other:Runnable):
        if(self.head):
            current = self.head
            while(current.next):
                current = current.next
        else:
            self.head = other

    def invoke(self,prompt:Any):
        current = self.head
        self.context = prompt
        while(current is not None):
            prompt = current.invoke(self.context)
            self.context = prompt
            current = current.next


  


