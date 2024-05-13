from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from tinychain.runnable.runnable_manager import Runnable


class JsonOutputParser(Runnable):
    def run(self, request: Any) -> str | None:
        return super().run(request)
    

class OutputParser(Runnable):
    def __init__(self) -> None:
        super().__init__()

    def invoke(self,input,input_schema="json"):
        print(f"parse {input}")
        return input