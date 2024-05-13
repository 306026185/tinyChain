# (current state and action) -> state 

from typing import Protocol
from rich.console import Console

console = Console()

# given light on -> switch
class LightState(Protocol):
    def switch(self,bulb)->None:
        ...

class OnState:
    def switch(self,bulb)->None:
        bulb.state = OffState()
        console.print("Light is [blue][bold] off [/]")

class OffState:
    def switch(self,bulb)->None:
        bulb.state = OnState()
        console.print("Light is [blue][bold] on [/]")
    

class Bulb:

    def __init__(self) -> None:
        self.state = OnState()

    def switch(self)->None:
        self.state.switch(self)


def main():
    bulb = Bulb()
    bulb.switch()
    bulb.switch()

if __name__ == "__main__":
    main()