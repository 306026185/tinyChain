import json

import uuid

from typing import Protocol,List,Optional,Union,Tuple
from dataclasses import dataclass



from tinychain.interface import AgentInterface
from tinychain.data_type import AgentState,Preset,LLMConfig,EmbeddingConfig,RecordMessage
from tinychain.utils import printd,verify_first_message_correctness

from tinychain.constants import (
    FIRST_MESSAGE_ATTEMPTS,
    JSON_LOADS_STRICT,
    MESSAGE_SUMMARY_WARNING_FRAC,
    MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC,
    MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST,
    CORE_MEMORY_HUMAN_CHAR_LIMIT,
    CORE_MEMORY_PERSONA_CHAR_LIMIT,
    LLM_MAX_TOKENS,
    CLI_WARNING_PREFIX,
    JSON_ENSURE_ASCII,
)

class Agent:

    def __init__(self,
        interface: AgentInterface,
        agent_state: Optional[AgentState] = None,
        preset: Optional[Preset] = None,
        created_by: Optional[uuid.UUID] = None,
        name: Optional[str] = None,
        llm_config: Optional[LLMConfig] = None,
        embedding_config: Optional[EmbeddingConfig] = None,
        messages_total: Optional[int] = None, 
        first_message_verify_mono: bool = True, 
        ) -> None:
        pass

    def step(
        self,
        user_message: Union[RecordMessage, str],  # NOTE: should be json.dump(dict)
        first_message: bool = False,
        first_message_retry_limit: int = FIRST_MESSAGE_ATTEMPTS,
        skip_verify: bool = False,
        return_dicts: bool = True,  # if True, return dicts, if False, return Message objects
    ) -> Tuple[List[Union[dict, RecordMessage]], bool, bool, bool]:
        try:
            # Step 0: add user message
            if user_message is not None:
                if isinstance(user_message, RecordMessage):
                    user_message_text = user_message.text
                elif isinstance(user_message, str):
                    user_message_text = user_message
                else:
                    raise ValueError(f"Bad type for user_message: {type(user_message)}")

                packed_user_message = {"role": "user", "content": user_message_text}
                # Special handling for AutoGen messages with 'name' field
                try:
                    user_message_json = json.loads(user_message_text, strict=JSON_LOADS_STRICT)
                    # Special handling for AutoGen messages with 'name' field
                    # Treat 'name' as a special field
                    # If it exists in the input message, elevate it to the 'message' level
                    if "name" in user_message_json:
                        packed_user_message["name"] = user_message_json["name"]
                        user_message_json.pop("name", None)
                        packed_user_message["content"] = json.dumps(user_message_json, ensure_ascii=JSON_ENSURE_ASCII)
                except Exception as e:
                    print(f"{CLI_WARNING_PREFIX}handling of 'name' field failed with: {e}")

                # Create the associated Message object (in the database)
                packed_user_message_obj = RecordMessage.dict_to_message(
                    agent_id=self.agent_state.id,
                    user_id=self.agent_state.user_id,
                    model=self.model,
                    openai_message_dict=packed_user_message,
                )
                self.interface.user_message(user_message_text, msg_obj=packed_user_message_obj)

                input_message_sequence = self.messages + [packed_user_message]
            # Alternatively, the requestor can send an empty user message
            else:
                input_message_sequence = self.messages
                packed_user_message = None

            if len(input_message_sequence) > 1 and input_message_sequence[-1]["role"] != "user":
                printd(f"{CLI_WARNING_PREFIX}Attempting to run ChatCompletion without user as the last message in the queue")

            # Step 1: send the conversation and available functions to GPT
            if not skip_verify and (first_message or self.messages_total == self.messages_total_init):
                printd(f"This is the first message. Running extra verifier on AI response.")
                counter = 0
                while True:
                    response = self._get_ai_reply(
                        message_sequence=input_message_sequence,
                        first_message=True,  # passed through to the prompt formatter
                    )
                    if verify_first_message_correctness(response, require_monologue=self.first_message_verify_mono):
                        break

                    counter += 1
                    if counter > first_message_retry_limit:
                        raise Exception(f"Hit first message retry limit ({first_message_retry_limit})")

            else:
                response = self._get_ai_reply(
                    message_sequence=input_message_sequence,
                )

            # Step 2: check if LLM wanted to call a function
            # (if yes) Step 3: call the function
            # (if yes) Step 4: send the info on the function call and function response to LLM
            response_message = response.choices[0].message
            response_message.copy()
            all_response_messages, heartbeat_request, function_failed = self._handle_ai_response(response_message)

            # Add the extra metadata to the assistant response
            # (e.g. enough metadata to enable recreating the API call)
            # assert "api_response" not in all_response_messages[0]
            # all_response_messages[0]["api_response"] = response_message_copy
            # assert "api_args" not in all_response_messages[0]
            # all_response_messages[0]["api_args"] = {
            #     "model": self.model,
            #     "messages": input_message_sequence,
            #     "functions": self.functions,
            # }

            # Step 4: extend the message history
            if user_message is not None:
                if isinstance(user_message, RecordMessage):
                    all_new_messages = [user_message] + all_response_messages
                else:
                    all_new_messages = [
                        RecordMessage.dict_to_message(
                            agent_id=self.agent_state.id,
                            user_id=self.agent_state.user_id,
                            model=self.model,
                            openai_message_dict=packed_user_message,
                        )
                    ] + all_response_messages
            else:
                all_new_messages = all_response_messages

            # Check the memory pressure and potentially issue a memory pressure warning
            current_total_tokens = response.usage.total_tokens
            active_memory_warning = False
            # We can't do summarize logic properly if context_window is undefined
            if self.agent_state.llm_config.context_window is None:
                # Fallback if for some reason context_window is missing, just set to the default
                print(f"{CLI_WARNING_PREFIX}could not find context_window in config, setting to default {LLM_MAX_TOKENS['DEFAULT']}")
                print(f"{self.agent_state}")
                self.agent_state.llm_config.context_window = (
                    LLM_MAX_TOKENS[self.model] if (self.model is not None and self.model in LLM_MAX_TOKENS) else LLM_MAX_TOKENS["DEFAULT"]
                )
            if current_total_tokens > MESSAGE_SUMMARY_WARNING_FRAC * int(self.agent_state.llm_config.context_window):
                printd(
                    f"{CLI_WARNING_PREFIX}last response total_tokens ({current_total_tokens}) > {MESSAGE_SUMMARY_WARNING_FRAC * int(self.agent_state.llm_config.context_window)}"
                )
                # Only deliver the alert if we haven't already (this period)
                if not self.agent_alerted_about_memory_pressure:
                    active_memory_warning = True
                    self.agent_alerted_about_memory_pressure = True  # it's up to the outer loop to handle this
            else:
                printd(
                    f"last response total_tokens ({current_total_tokens}) < {MESSAGE_SUMMARY_WARNING_FRAC * int(self.agent_state.llm_config.context_window)}"
                )

            self._append_to_messages(all_new_messages)
            messages_to_return = [msg.to_openai_dict() for msg in all_new_messages] if return_dicts else all_new_messages
            return messages_to_return, heartbeat_request, function_failed, active_memory_warning, response.usage.completion_tokens

        except Exception as e:
            printd(f"step() failed\nuser_message = {user_message}\nerror = {e}")

            # If we got a context alert, try trimming the messages length, then try again
            if is_context_overflow_error(e):
                # A separate API call to run a summarizer
                self.summarize_messages_inplace()

                # Try step again
                return self.step(user_message, first_message=first_message, return_dicts=return_dicts)
            else:
                printd(f"step() failed with an unrecognized exception: '{str(e)}'")
                raise e