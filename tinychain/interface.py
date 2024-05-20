import json
from typing import List, Optional
from abc import ABC, abstractmethod

from tinychain.data_type import RecordMessage

class AgentInterface(ABC):

    @abstractmethod
    def user_message(self, msg: str, msg_obj: Optional[RecordMessage] = None):
        """MemGPT receives a user message"""
        raise NotImplementedError

    @abstractmethod
    def internal_monologue(self, msg: str, msg_obj: Optional[RecordMessage] = None):
        """MemGPT generates some internal monologue"""
        raise NotImplementedError

    @abstractmethod
    def assistant_message(self, msg: str, msg_obj: Optional[RecordMessage] = None):
        """MemGPT uses send_message"""
        raise NotImplementedError

    @abstractmethod
    def function_message(self, msg: str, msg_obj: Optional[RecordMessage] = None):
        """MemGPT calls a function"""
        raise NotImplementedError