from typing import Any,Optional

from tinychain.local_llm.ollama.api import get_ollama_completion
from tinychain.local_llm.llm_chat_completion_wrappers.simple_summary_wrapper import SimpleSummaryWrapper

from tinychain.utils import printd


WORD_LIMIT = 100
SUMMARIZE_SYSTEM_MESSAGE = f"""
Your job is to summarize a history of previous messages in a conversation between an AI persona and a human.
The conversation you are given is a from a fixed context window and may not be complete.
Messages sent by the AI are marked with the 'assistant' role.
The AI 'assistant' can also make calls to functions, whose outputs can be seen in messages with the 'function' role.
Things the AI says in the message content are considered inner monologue and are not seen by the user.
The only AI messages seen by the user are from when the AI uses 'send_message'.
Messages the user sends are in the 'user' role.
The 'user' role is also used for important system events, such as login events and heartbeat events (heartbeats run the AI's program without user action, allowing the AI to act without prompting from the user sending them a message).
Summarize what happened in the conversation from the perspective of the AI (use the first person).
Keep your summary less than {WORD_LIMIT} words, do NOT exceed this word limit.
Only output the summary, do NOT include anything else in your output.
"""


def get_chat_completion(
    model_name:str,
    messages:Any,
    functions=None,
    functions_python=None,
    wrapper=None,
    function_call="auto",
    first_message=False,
    endpoint:Optional[str]=None,
    context_window:Optional[int]=None,
    endpoint_type:Optional[str]=None):

    # messages -> prompt

    """
    messages = [
    {"role":"system":"content":"system decription"},
    {"role":"assistant":"content":"assistant decription"},
    ]
    
    """

    documentation = None

    if messages[0]["role"] == "system" and messages[0]["content"].strip() == SUMMARIZE_SYSTEM_MESSAGE.strip():
        llm_wrapper = SimpleSummaryWrapper()

    
    prompt = llm_wrapper.chat_completion_to_prompt(messages=messages, functions=functions, function_documentation=documentation)
    
    printd(prompt)

    if endpoint_type == "ollama":
        result, usage = get_ollama_completion(endpoint,model_name,prompt,context_window=context_window)

    # result -> response
    else:
        raise

    if result is None or result == "":
        raise

    chat_completion_result = llm_wrapper.output_to_chat_completion_response(result)

    if not ("prompt_tokens" in usage and "completion_tokens" in usage and "total_tokens" in usage):
        raise





if __name__ =="__main__":

    context_window = 8192
    endpoint = "http://localhost:11434"
    model_name = "llama3:latest"
    get_chat_completion(model_name=model_name,
                        endpoint_type="ollama",
                        messages=[
        {"role":"system","content":SUMMARIZE_SYSTEM_MESSAGE},
        {"role":"assistant","content":"you are very help assistatn"},
        {"role":"user","content":"write hello world programming in python"},
    ],endpoint=endpoint,
        context_window=context_window)