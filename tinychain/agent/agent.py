from typing import Protocol,List
from dataclasses import dataclass


class AgentState(Protocol):

    # query llm with prompt
    def query(self):
        ...

    # waiting form human feedback
    def review(self):
        ...

    # finalize
    def finalize(self):
        ...


class AgentContext(Protocol):
    messages:List[str]

    def set_state(self,state:AgentState) -> None:
        ...

    def query(self):
        ...

    def review(self):
        ...

    def finalize(self):
        ...

    def show_messages(self):
        ...

@dataclass
class Prompt(AgentState):
    context:AgentContext

    def query(self):
        print("query llm with prompt")
        #  get prompt
        # ask llm with prompt
        self.context.messages.append("prompt and response")

    def review(self):
        # huminput

        self.context.set_state(Review(self.context))

    def finalize(self):

@dataclass
class Review(AgentState):
    context:AgentContext
