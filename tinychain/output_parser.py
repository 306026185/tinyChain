from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from runnable_manager import AbstractRunnable

class JsonOutputParser(AbstractRunnable):
    def run(self, request: Any) -> str | None:
        return super().run(request)