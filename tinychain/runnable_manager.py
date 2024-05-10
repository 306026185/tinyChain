from __future__ import annotations
from abc import ABC,abstractmethod
from typing import Any, Optional

class Runnable(ABC):

    @abstractmethod
    def set_next(self,runnable:Runnable)->Runnable:
        pass

    @abstractmethod
    def run(self,request:Any)->Optional[str]:
        pass


class AbstractRunnable(Runnable):

    _next_runnable:Runnable = None

    def set_next(self, runnable: Runnable) -> Runnable:
        self._next_runnable = runnable
        return runnable
    
    @abstractmethod
    def run(self, request: Any) -> str | None:
        if self._next_runnable:
            return self._next_runnable(request)
        
        return None