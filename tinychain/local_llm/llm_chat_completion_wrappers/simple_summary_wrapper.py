import json

from tinychain.local_llm.llm_chat_completion_wrappers.wrapper_base import LLMChatCompletionWrapper

JSON_LOADS_STRICT = False
JSON_ENSURE_ASCII = False


# prompt_chain(tiny,FP,java,js,c/cpp,rust,go,scala) -> tinychain(simple,go) -> azent(企业级)
class SimpleSummaryWrapper(LLMChatCompletionWrapper):

    def __init__(self,
                 simplify_json_content=True,
                 include_assistant_prefix=True,
                 include_section_separators=True) -> None:
        
        self.simplify_json_content = simplify_json_content
        self.include_assistant_prefix = include_assistant_prefix
        self.include_section_separators = include_section_separators

    def chat_completion_to_prompt(self, messages, functions, function_documentation=None):
        """
        OpenAI functions schema style:

            {
                "name": "send_message",
                "description": "Sends a message to the human user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        # https://json-schema.org/understanding-json-schema/reference/array.html
                        "message": {
                            "type": "string",
                            "description": "Message contents. All unicode (including emojis) are supported.",
                        },
                    },
                    "required": ["message"],
                }
            },
        """

        prompt = ""
        assert messages[0]["role"] == "system"
        prompt += messages[0]["content"]
        """
        ChatCompletion data (inside message['function_call']):
                "function_call": {
                    "name": ...
                    "arguments": {
                        "arg1": val1,
                        ...
                    }

            """
        
        def create_function_call(function_call):

            func_call = {
                "function": function_call["name"],
                "params": json.loads(function_call["arguments"], strict=JSON_LOADS_STRICT),
            }

            return json.dumps(func_call,indent=2,ensure_ascii=JSON_ENSURE_ASCII)
        
        if self.include_section_separators:
            prompt += "\n### INPUT"

        for message in messages[1:]:
            assert message["role"] in ["user", "assistant", "function", "tool"], message
            if message["role"] == "user":
                if self.simplify_json_content:
                    try:
                        content_json = json.loads(message["content"], strict=JSON_LOADS_STRICT)
                        content_simple = content_json["message"]
                        prompt += f"\nUSER: {content_simple}"
                    except:
                        prompt += f"\nUSER: {message['content']}"
                elif message["role"] == "assistant":
                    prompt += f"\nASSISTANT: {message['content']}"
                    # need to add the function call if there was one
                    if message["function_call"]:
                        prompt += f"\n{create_function_call(message['function_call'])}"

                elif message["role"] in ["function", "tool"]:
                    # TODO find a good way to add this
                    # prompt += f"\nASSISTANT: (function return) {message['content']}"
                    prompt += f"\nFUNCTION RETURN: {message['content']}"
                    continue
                else:
                    raise ValueError(message)

        if self.include_section_separators:
            prompt += "\n### RESPONSE (your summary of the above conversation in plain English (no JSON!), do NOT exceed the word limit)"
 
        if self.include_assistant_prefix:
            prompt += f"\nSUMMARY:"

        return prompt
            
    def output_to_chat_completion_response(self, raw_llm_output):
        """Turn raw LLM output into a ChatCompletion style response with:
        "message" = {
            "role": "assistant",
            "content": ...,
            "function_call": {
                "name": ...
                "arguments": {
                    "arg1": val1,
                    ...
                }
            }
        }
        """
        raw_llm_output = raw_llm_output.strip()
        message = {
            "role":"assistant",
            "content":raw_llm_output
        }

        return message
    

if __name__ == "__main__":
    pass