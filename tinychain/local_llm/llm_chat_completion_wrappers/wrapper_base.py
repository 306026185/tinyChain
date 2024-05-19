from abc import ABC,abstractmethod

class LLMChatCompletionWrapper(ABC):
    @abstractmethod
    def chat_completion_to_prompt(self, messages, functions, function_documentation=None):
        """completion convert to single prompt"""

    @abstractmethod
    def output_to_chat_completion_response(self, raw_llm_output):
        """LLM output string convert to a ChatCompletion response"""