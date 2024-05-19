import json

from tinychain.local_llm.llm_chat_completion_wrappers.wrapper_base import LLMChatCompletionWrapper
class ChatMLInnerMonologueWrapper(LLMChatCompletionWrapper):
    

    def chat_completion_to_prompt(self, messages, functions, first_message=False, function_documentation=None):
        pass

    def output_to_chat_completion_response(self, raw_llm_output, first_message=False):
        pass