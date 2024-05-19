import random
import time
import requests
import time
from typing import Union

import uuid
import urllib

from tinychain.constants import CLI_WARNING_PREFIX,DEFAULT_PERSONA,DEFAULT_HUMAN,DEFAULT_PRESET
from tinychain.utils import printd,get_human_text,get_persona_text

from tinychain.data_type import AgentState,LLMConfig,EmbeddingConfig
from tinychain.model.chat_completion_response import ChatCompletionResponse
from tinychain.local_llm.chat_completion_proxy import get_chat_completion,SUMMARIZE_SYSTEM_MESSAGE
from tinychain.data_type import Preset



def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 10,
    error_codes: tuple = (429,),
):
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):

        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                # wrapper post request
                return func(*args, **kwargs)

            except requests.exceptions.HTTPError as http_err:
                # Retry on specified errors
                if http_err.response.status_code in error_codes:
                    # Increment retries
                    num_retries += 1

                    # Check if max retries has been reached
                    if num_retries > max_retries:
                        raise Exception(f"Maximum number of retries ({max_retries}) exceeded.")

                    # Increment the delay
                    delay *= exponential_base * (1 + jitter * random.random())

                    # Sleep for the delay
                    # printd(f"Got a rate limit error ('{http_err}') on LLM backend request, waiting {int(delay)}s then retrying...")
                    print(
                        f"{CLI_WARNING_PREFIX}Got a rate limit error ('{http_err}') on LLM backend request, waiting {int(delay)}s then retrying..."
                    )
                    time.sleep(delay)
                else:
                    # For other HTTP errors, re-raise the exception
                    raise

            # Raise exceptions for any errors not specified
            except Exception as e:
                raise e

    return wrapper

@retry_with_exponential_backoff
def create(
    agent_state: AgentState,
    messages,
    functions=None,
    functions_python=None,
    function_call="auto",
    first_message=False,
) -> ChatCompletionResponse:
    
    printd(f"Using model {agent_state.llm_config.model_endpoint_type}, endpoint: {agent_state.llm_config.model_endpoint}")


    if function_call and not functions:
        printd("unsetting function_call because functions is None")
        function_call = None

    return get_chat_completion(
            model_name=agent_state.llm_config.model,
            messages=messages,
            functions=functions,
            functions_python=functions_python,
            function_call=function_call,
            context_window=agent_state.llm_config.context_window,
            endpoint=agent_state.llm_config.model_endpoint,
            wrapper=agent_state.llm_config.model_wrapper,
            first_message=first_message,
        )
if __name__ == "__main__":

    name = "temp"
    persona = "tinychain_starter.txt"
    human ="zidea.txt"
    llm_config = LLMConfig()
    embedding_config = EmbeddingConfig()
    
    preset = Preset(
            user_id=uuid.uuid4,
            name=DEFAULT_PRESET,
            system=SUMMARIZE_SYSTEM_MESSAGE,
            persona=get_persona_text(DEFAULT_PERSONA),
            persona_name=DEFAULT_PERSONA,
            human=get_human_text(DEFAULT_HUMAN),
            human_name=DEFAULT_HUMAN,
            functions_schema=functions_schema,
        )

    preset
    agent_state = AgentState()


    create()