# state machine

from __future__ import annotations
from abc import ABC, abstractmethod

class State(ABC):
    @property
    def context(self) -> Context:
        return self._context

    @context.setter
    def context(self, context: Context) -> None:
        self._context = context

    @abstractmethod
    def doSomething(self) -> None:
        pass

class Context:
    _state = None


    def __init__(self,state:State) -> None:
        self.setState(state)

    def setState(self, state: State):
        print(f"Context: Transitioning to {type(state).__name__}")
        self._state = state
        self._state.context = self

    def ask(self,prompt): 
        self._state.doSomething()

    def aask(self):
        self._state.doSomething()

class ConcreteStateA(State):
    def doSomething(self) -> None:
        print("The context is in the state of ConcreteStateA.")
        print("ConcreteStateA now changes the state of the context.")
        self.context.setState(ConcreteStateB())


class ConcreteStateB(State):
    def doSomething(self) -> None:
        print("The context is in the state of ConcreteStateB.")
        print("ConcreteStateB wants to change the state of the context.")
        self.context.setState(ConcreteStateA())


if __name__ == "__main__":
    agent = Context(ConcreteStateA())
    agent.ask()    # this method is executed as in state 1
    agent.ask() 
