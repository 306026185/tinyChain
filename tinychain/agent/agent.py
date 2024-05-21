import json

import uuid
from datetime import datetime
import inspect
import traceback
from tqdm import tqdm
from pathlib import Path
from typing import Protocol,List,Optional,Union,Tuple,cast
from dataclasses import dataclass
from tinychain.llm_api.llm_api_tools import create, is_context_overflow_error
from tinychain.memory import CoreMemory as InContextMemory
from tinychain.memory import ArchivalMemory,RecallMemory,summarize_messages
from tinychain.interface import AgentInterface
from tinychain.data_type import AgentState,Preset,LLMConfig,EmbeddingConfig,RecordMessage
from tinychain.utils import printd,verify_first_message_correctness
from tinychain.model import  chat_completion_response
from tinychain.persistence_manager import LocalStateManager
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

from tinychain.utils import (
    count_tokens,
    create_random_username,
    create_uuid_from_string,
    get_local_time,
    get_schema_diff,
    get_tool_call_id,
    get_utc_time,
    is_utc_datetime,
    parse_json,
    printd,
    united_diff,
    validate_function_response,
    verify_first_message_correctness,
)

from tinychain.data_type import (
    AgentState,
    EmbeddingConfig,
    LLMConfig,
    RecordMessage,
    Passage,
    Preset,
)
from tinychain.system import (
    get_initial_boot_messages,
    get_login_event,
    package_function_response,
    package_summarize_message,
)

from tinychain.functions.functions import USER_FUNCTIONS_DIR,load_all_function_sets

def link_functions(function_schemas: list):
    """Link function definitions to list of function schemas"""

    # need to dynamically link the functions
    # the saved agent.functions will just have the schemas, but we need to
    # go through the functions library and pull the respective python functions

    # Available functions is a mapping from:
    # function_name -> {
    #   json_schema: schema
    #   python_function: function
    # }
    # agent.functions is a list of schemas (OpenAI kwarg functions style, see: https://platform.openai.com/docs/api-reference/chat/create)
    # [{'name': ..., 'description': ...}, {...}]
    available_functions = load_all_function_sets()
    linked_function_set = {}
    for f_schema in function_schemas:
        # Attempt to find the function in the existing function library
        f_name = f_schema.get("name")
        if f_name is None:
            raise ValueError(f"While loading agent.state.functions encountered a bad function schema object with no name:\n{f_schema}")
        linked_function = available_functions.get(f_name)
        if linked_function is None:
            raise ValueError(
                f"Function '{f_name}' was specified in agent.state.functions, but is not in function library:\n{available_functions.keys()}"
            )
        # Once we find a matching function, make sure the schema is identical
        if json.dumps(f_schema, ensure_ascii=JSON_ENSURE_ASCII) != json.dumps(
            linked_function["json_schema"], ensure_ascii=JSON_ENSURE_ASCII
        ):
            # error_message = (
            #     f"Found matching function '{f_name}' from agent.state.functions inside function library, but schemas are different."
            #     + f"\n>>>agent.state.functions\n{json.dumps(f_schema, indent=2, ensure_ascii=JSON_ENSURE_ASCII)}"
            #     + f"\n>>>function library\n{json.dumps(linked_function['json_schema'], indent=2, ensure_ascii=JSON_ENSURE_ASCII)}"
            # )
            schema_diff = get_schema_diff(f_schema, linked_function["json_schema"])
            error_message = (
                f"Found matching function '{f_name}' from agent.state.functions inside function library, but schemas are different.\n"
                + "".join(schema_diff)
            )

            # NOTE to handle old configs, instead of erroring here let's just warn
            # raise ValueError(error_message)
            printd(error_message)
        linked_function_set[f_name] = linked_function
    return linked_function_set

def initialize_memory(ai_notes: Union[str, None], human_notes: Union[str, None]):
    if ai_notes is None:
        raise ValueError(ai_notes)
    if human_notes is None:
        raise ValueError(human_notes)
    memory = InContextMemory(human_char_limit=CORE_MEMORY_HUMAN_CHAR_LIMIT, persona_char_limit=CORE_MEMORY_PERSONA_CHAR_LIMIT)
    memory.edit_persona(ai_notes)
    memory.edit_human(human_notes)
    return memory

def construct_system_with_memory(
    system: str,
    memory: InContextMemory,
    memory_edit_timestamp: str,
    archival_memory: Optional[ArchivalMemory] = None,
    recall_memory: Optional[RecallMemory] = None,
    include_char_count: bool = True,
):
    full_system_message = "\n".join(
        [
            system,
            "\n",
            f"### Memory [last modified: {memory_edit_timestamp.strip()}]",
            f"{len(recall_memory) if recall_memory else 0} previous messages between you and the user are stored in recall memory (use functions to access them)",
            f"{len(archival_memory) if archival_memory else 0} total memories you created are stored in archival memory (use functions to access them)",
            "\nCore memory shown below (limited in size, additional information stored in archival / recall memory):",
            f'<persona characters="{len(memory.persona)}/{memory.persona_char_limit}">' if include_char_count else "<persona>",
            memory.persona,
            "</persona>",
            f'<human characters="{len(memory.human)}/{memory.human_char_limit}">' if include_char_count else "<human>",
            memory.human,
            "</human>",
        ]
    )
    return full_system_message

def initialize_message_sequence(
    model: str,
    system: str,
    memory: InContextMemory,
    archival_memory: Optional[ArchivalMemory] = None,
    recall_memory: Optional[RecallMemory] = None,
    memory_edit_timestamp: Optional[str] = None,
    include_initial_boot_message: bool = True,
) -> List[dict]:
    if memory_edit_timestamp is None:
        memory_edit_timestamp = get_local_time()

    full_system_message = construct_system_with_memory(
        system, memory, memory_edit_timestamp, archival_memory=archival_memory, recall_memory=recall_memory
    )
    first_user_message = get_login_event()  # event letting MemGPT know the user just logged in

    if include_initial_boot_message:
        initial_boot_messages = get_initial_boot_messages("startup_with_send_message")
        messages = (
            [
                {"role": "system", "content": full_system_message},
            ]
            + initial_boot_messages
            + [
                {"role": "user", "content": first_user_message},
            ]
        )

    else:
        messages = [
            {"role": "system", "content": full_system_message},
            {"role": "user", "content": first_user_message},
        ]

    return messages

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
        
        if preset is not None:
            assert agent_state is None, "Can create an agent from a Preset or AgentState (but both were provided)"
            assert created_by is not None, "Must provide created_by field when creating an Agent from a Preset"
            assert llm_config is not None, "Must provide llm_config field when creating an Agent from a Preset"
            assert embedding_config is not None, "Must provide embedding_config field when creating an Agent from a Preset"

            # if agent_state is also provided, override any preset values
            init_agent_state = AgentState(
                name=name,
                user_id=created_by,
                persona=preset.persona_name,
                human=preset.human_name,
                llm_config=llm_config,
                embedding_config=embedding_config,
                preset=preset.name,  # TODO link via preset.id instead of name?
                state={
                    "persona": preset.persona,
                    "human": preset.human,
                    "system": preset.system,
                    "functions": preset.functions_schema,
                    "messages": None,
                },
            )

        elif agent_state is not None:
            assert preset is None, "Can create an agent from a Preset or AgentState (but both were provided)"
            assert agent_state.state is not None and agent_state.state != {}, "AgentState.state cannot be empty"

            # Assume the agent_state passed in is formatted correctly
            init_agent_state = agent_state

        else:
            raise ValueError("Both Preset and AgentState were null (must provide one or the other)")

        self.agent_state = init_agent_state

        self.model = self.agent_state.llm_config.model

        if "system" not in self.agent_state.state:
            raise ValueError("'system' not found in provided AgentState")
        self.system = self.agent_state.state["system"]

        if "functions" not in self.agent_state.state:
            raise ValueError(f"'functions' not found in provided AgentState")
        self.functions = self.agent_state.state["functions"]
    
        self.functions_python = {k: v["python_function"] for k, v in link_functions(function_schemas=self.functions).items()}


        # Initialize the memory object
        if "persona" not in self.agent_state.state:
            raise ValueError(f"'persona' not found in provided AgentState")
        if "human" not in self.agent_state.state:
            raise ValueError(f"'human' not found in provided AgentState")
        self.memory = initialize_memory(ai_notes=self.agent_state.state["persona"], human_notes=self.agent_state.state["human"])

        # Interface must implement:
        # - internal_monologue
        # - assistant_message
        # - function_message
        # ...
        # Different interfaces can handle events differently
        # e.g., print in CLI vs send a discord message with a discord bot
        self.interface = interface

        # Create the persistence manager object based on the AgentState info
        # TODO
        self.persistence_manager = LocalStateManager(agent_state=self.agent_state)

        # State needed for heartbeat pausing
        self.pause_heartbeats_start = None
        self.pause_heartbeats_minutes = 0

        self.first_message_verify_mono = first_message_verify_mono

        # Controls if the convo memory pressure warning is triggered
        # When an alert is sent in the message queue, set this to True (to avoid repeat alerts)
        # When the summarizer is run, set this back to False (to reset)
        self.agent_alerted_about_memory_pressure = False

        self._messages: List[RecordMessage] = []

        # Once the memory object is initialized, use it to "bake" the system message
        if "messages" in self.agent_state.state and self.agent_state.state["messages"] is not None:
            # print(f"Agent.__init__ :: loading, state={agent_state.state['messages']}")
            if not isinstance(self.agent_state.state["messages"], list):
                raise ValueError(f"'messages' in AgentState was bad type: {type(self.agent_state.state['messages'])}")
            assert all([isinstance(msg, str) for msg in self.agent_state.state["messages"]])

            # Convert to IDs, and pull from the database
            raw_messages = [
                self.persistence_manager.recall_memory.storage.get(id=uuid.UUID(msg_id)) for msg_id in self.agent_state.state["messages"]
            ]
            assert all([isinstance(msg, RecordMessage) for msg in raw_messages]), (raw_messages, self.agent_state.state["messages"])
            self._messages.extend([cast(RecordMessage, msg) for msg in raw_messages if msg is not None])

            for m in self._messages:
                # assert is_utc_datetime(m.created_at), f"created_at on message for agent {self.agent_state.name} isn't UTC:\n{vars(m)}"
                # TODO eventually do casting via an edit_message function
                if not is_utc_datetime(m.created_at):
                    printd(f"Warning - created_at on message for agent {self.agent_state.name} isn't UTC (text='{m.text}')")
                    m.created_at = m.created_at.replace(tzinfo=datetime.timezone.utc)

        else:
            # print(f"Agent.__init__ :: creating, state={agent_state.state['messages']}")
            init_messages = initialize_message_sequence(
                self.model,
                self.system,
                self.memory,
            )
            init_messages_objs = []
            for msg in init_messages:
                init_messages_objs.append(
                    RecordMessage.dict_to_message(
                        agent_id=self.agent_state.id, user_id=self.agent_state.user_id, model=self.model, openai_message_dict=msg
                    )
                )
            assert all([isinstance(msg, RecordMessage) for msg in init_messages_objs]), (init_messages_objs, init_messages)
            self.messages_total = 0
            self._append_to_messages(added_messages=[cast(RecordMessage, msg) for msg in init_messages_objs if msg is not None])

            for m in self._messages:
                assert is_utc_datetime(m.created_at), f"created_at on message for agent {self.agent_state.name} isn't UTC:\n{vars(m)}"
                # TODO eventually do casting via an edit_message function
                if not is_utc_datetime(m.created_at):
                    printd(f"Warning - created_at on message for agent {self.agent_state.name} isn't UTC (text='{m.text}')")
                    m.created_at = m.created_at.replace(tzinfo=datetime.timezone.utc)

        # Keep track of the total number of messages throughout all time
        self.messages_total = messages_total if messages_total is not None else (len(self._messages) - 1)  # (-system)
        # self.messages_total_init = self.messages_total
        self.messages_total_init = len(self._messages) - 1
        printd(f"Agent initialized, self.messages_total={self.messages_total}")

        # Create the agent in the DB
        # self.save()
        self.update_state()
    
    @property
    def messages(self) -> List[dict]:
        """Getter method that converts the internal RecordMessage list into OpenAI-style dicts"""
        return [msg.to_openai_dict() for msg in self._messages]

    @messages.setter
    def messages(self, value):
        raise Exception("Modifying message list directly not allowed")

    def _trim_messages(self, num):
        """Trim messages from the front, not including the system message"""
        self.persistence_manager.trim_messages(num)

        new_messages = [self._messages[0]] + self._messages[num:]
        self._messages = new_messages

    def _prepend_to_messages(self, added_messages: List[RecordMessage]):
        """Wrapper around self.messages.prepend to allow additional calls to a state/persistence manager"""
        assert all([isinstance(msg, RecordMessage) for msg in added_messages])

        self.persistence_manager.prepend_to_messages(added_messages)

        new_messages = [self._messages[0]] + added_messages + self._messages[1:]  # prepend (no system)
        self._messages = new_messages
        self.messages_total += len(added_messages)  # still should increment the message counter (summaries are additions too)

    def _append_to_messages(self, added_messages: List[RecordMessage]):
        """Wrapper around self.messages.append to allow additional calls to a state/persistence manager"""
        assert all([isinstance(msg, RecordMessage) for msg in added_messages])

        self.persistence_manager.append_to_messages(added_messages)

        # strip extra metadata if it exists
        # for msg in added_messages:
        # msg.pop("api_response", None)
        # msg.pop("api_args", None)
        new_messages = self._messages + added_messages  # append

        self._messages = new_messages
        self.messages_total += len(added_messages)

    def append_to_messages(self, added_messages: List[dict]):
        """An external-facing message append, where dict-like messages are first converted to RecordMessage objects"""
        added_messages_objs = [
            RecordMessage.dict_to_message(
                agent_id=self.agent_state.id,
                user_id=self.agent_state.user_id,
                model=self.model,
                openai_message_dict=msg,
            )
            for msg in added_messages
        ]
        self._append_to_messages(added_messages_objs)

    def _swap_system_message(self, new_system_message: RecordMessage):
        assert isinstance(new_system_message, RecordMessage)
        assert new_system_message.role == "system", new_system_message
        assert self._messages[0].role == "system", self._messages

        self.persistence_manager.swap_system_message(new_system_message)

        new_messages = [new_system_message] + self._messages[1:]  # swap index 0 (system)
        self._messages = new_messages

    def _get_ai_reply(
        self,
        message_sequence: List[RecordMessage],
        function_call: str = "auto",
        first_message: bool = False,  # hint
        stream: bool = False,  # TODO move to config?
    ) -> chat_completion_response.ChatCompletionResponse:
        """Get response from LLM API"""
        try:
            response = create(
                # agent_state=self.agent_state,
                llm_config=self.agent_state.llm_config,
                user_id=self.agent_state.user_id,
                messages=message_sequence,
                functions=self.functions,
                functions_python=self.functions_python,
                function_call=function_call,
                # hint
                first_message=first_message,
                # streaming
                stream=stream,
                stream_inferface=self.interface,
            )
            # special case for 'length'
            if response.choices[0].finish_reason == "length":
                raise Exception("Finish reason was length (maximum context length)")

            # catches for soft errors
            if response.choices[0].finish_reason not in ["stop", "function_call", "tool_calls"]:
                raise Exception(f"API call finish with bad finish reason: {response}")

            # unpack with response.choices[0].message.content
            return response
        except Exception as e:
            raise e

    def _handle_ai_response(
        self, response_message: chat_completion_response.RecordMessage, override_tool_call_id: bool = True
    ) -> Tuple[List[RecordMessage], bool, bool]:
        """Handles parsing and function execution"""

        messages = []  # append these to the history when done

        # Step 2: check if LLM wanted to call a function
        if response_message.function_call or (response_message.tool_calls is not None and len(response_message.tool_calls) > 0):
            if response_message.function_call:
                raise DeprecationWarning(response_message)
            if response_message.tool_calls is not None and len(response_message.tool_calls) > 1:
                # raise NotImplementedError(f">1 tool call not supported")
                # TODO eventually support sequential tool calling
                printd(f">1 tool call not supported, using index=0 only\n{response_message.tool_calls}")
                response_message.tool_calls = [response_message.tool_calls[0]]
            assert response_message.tool_calls is not None and len(response_message.tool_calls) > 0

            # generate UUID for tool call
            if override_tool_call_id or response_message.function_call:
                tool_call_id = get_tool_call_id()  # needs to be a string for JSON
                response_message.tool_calls[0].id = tool_call_id
            else:
                tool_call_id = response_message.tool_calls[0].id
                assert tool_call_id is not None  # should be defined

            # only necessary to add the tool_cal_id to a function call (antipattern)
            # response_message_dict = response_message.model_dump()
            # response_message_dict["tool_call_id"] = tool_call_id

            # role: assistant (requesting tool call, set tool call ID)
            messages.append(
                # NOTE: we're recreating the message here
                # TODO should probably just overwrite the fields?
                RecordMessage.dict_to_message(
                    agent_id=self.agent_state.id,
                    user_id=self.agent_state.user_id,
                    model=self.model,
                    openai_message_dict=response_message.model_dump(),
                )
            )  # extend conversation with assistant's reply
            printd(f"Function call message: {messages[-1]}")

            # The content if then internal monologue, not chat
            self.interface.internal_monologue(response_message.content, msg_obj=messages[-1])

            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors

            # Failure case 1: function name is wrong
            function_call = (
                response_message.function_call if response_message.function_call is not None else response_message.tool_calls[0].function
            )
            function_name = function_call.name
            printd(f"Request to call function {function_name} with tool_call_id: {tool_call_id}")
            try:
                function_to_call = self.functions_python[function_name]
            except KeyError as e:
                error_msg = f"No function named {function_name}"
                function_response = package_function_response(False, error_msg)
                messages.append(
                    RecordMessage.dict_to_message(
                        agent_id=self.agent_state.id,
                        user_id=self.agent_state.user_id,
                        model=self.model,
                        openai_message_dict={
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                            "tool_call_id": tool_call_id,
                        },
                    )
                )  # extend conversation with function response
                self.interface.function_message(f"Error: {error_msg}", msg_obj=messages[-1])
                return messages, False, True  # force a heartbeat to allow agent to handle error

            # Failure case 2: function name is OK, but function args are bad JSON
            try:
                raw_function_args = function_call.arguments
                function_args = parse_json(raw_function_args)
            except Exception as e:
                error_msg = f"Error parsing JSON for function '{function_name}' arguments: {function_call.arguments}"
                function_response = package_function_response(False, error_msg)
                messages.append(
                    RecordMessage.dict_to_message(
                        agent_id=self.agent_state.id,
                        user_id=self.agent_state.user_id,
                        model=self.model,
                        openai_message_dict={
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                            "tool_call_id": tool_call_id,
                        },
                    )
                )  # extend conversation with function response
                self.interface.function_message(f"Error: {error_msg}", msg_obj=messages[-1])
                return messages, False, True  # force a heartbeat to allow agent to handle error

            # (Still parsing function args)
            # Handle requests for immediate heartbeat
            heartbeat_request = function_args.pop("request_heartbeat", None)
            if not (isinstance(heartbeat_request, bool) or heartbeat_request is None):
                printd(
                    f"{CLI_WARNING_PREFIX}'request_heartbeat' arg parsed was not a bool or None, type={type(heartbeat_request)}, value={heartbeat_request}"
                )
                heartbeat_request = False

            # Failure case 3: function failed during execution
            # NOTE: the msg_obj associated with the "Running " message is the prior assistant message, not the function/tool role message
            #       this is because the function/tool role message is only created once the function/tool has executed/returned
            self.interface.function_message(f"Running {function_name}({function_args})", msg_obj=messages[-1])
            try:
                spec = inspect.getfullargspec(function_to_call).annotations

                for name, arg in function_args.items():
                    if isinstance(function_args[name], dict):
                        function_args[name] = spec[name](**function_args[name])

                function_args["self"] = self  # need to attach self to arg since it's dynamically linked

                function_response = function_to_call(**function_args)
                if function_name in ["conversation_search", "conversation_search_date", "archival_memory_search"]:
                    # with certain functions we rely on the paging mechanism to handle overflow
                    truncate = False
                else:
                    # but by default, we add a truncation safeguard to prevent bad functions from
                    # overflow the agent context window
                    truncate = True
                function_response_string = validate_function_response(function_response, truncate=truncate)
                function_args.pop("self", None)
                function_response = package_function_response(True, function_response_string)
                function_failed = False
            except Exception as e:
                function_args.pop("self", None)
                # error_msg = f"Error calling function {function_name} with args {function_args}: {str(e)}"
                # Less detailed - don't provide full args, idea is that it should be in recent context so no need (just adds noise)
                error_msg = f"Error calling function {function_name}: {str(e)}"
                error_msg_user = f"{error_msg}\n{traceback.format_exc()}"
                printd(error_msg_user)
                function_response = package_function_response(False, error_msg)
                messages.append(
                    RecordMessage.dict_to_message(
                        agent_id=self.agent_state.id,
                        user_id=self.agent_state.user_id,
                        model=self.model,
                        openai_message_dict={
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                            "tool_call_id": tool_call_id,
                        },
                    )
                )  # extend conversation with function response
                self.interface.function_message(f"Ran {function_name}({function_args})", msg_obj=messages[-1])
                self.interface.function_message(f"Error: {error_msg}", msg_obj=messages[-1])
                return messages, False, True  # force a heartbeat to allow agent to handle error

            # If no failures happened along the way: ...
            # Step 4: send the info on the function call and function response to GPT
            messages.append(
                RecordMessage.dict_to_message(
                    agent_id=self.agent_state.id,
                    user_id=self.agent_state.user_id,
                    model=self.model,
                    openai_message_dict={
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                        "tool_call_id": tool_call_id,
                    },
                )
            )  # extend conversation with function response
            self.interface.function_message(f"Ran {function_name}({function_args})", msg_obj=messages[-1])
            self.interface.function_message(f"Success: {function_response_string}", msg_obj=messages[-1])

        else:
            # Standard non-function reply
            messages.append(
                RecordMessage.dict_to_message(
                    agent_id=self.agent_state.id,
                    user_id=self.agent_state.user_id,
                    model=self.model,
                    openai_message_dict=response_message.model_dump(),
                )
            )  # extend conversation with assistant's reply
            self.interface.internal_monologue(response_message.content, msg_obj=messages[-1])
            heartbeat_request = False
            function_failed = False

        return messages, heartbeat_request, function_failed
    def step(
        self,
        user_message: Union[RecordMessage, str],  # NOTE: should be json.dump(dict)
        first_message: bool = False,
        first_message_retry_limit: int = FIRST_MESSAGE_ATTEMPTS,
        skip_verify: bool = False,
        return_dicts: bool = True,  # if True, return dicts, if False, return RecordMessage objects
    ) -> Tuple[List[Union[dict, RecordMessage]], bool, bool, bool]:
        try:
            # Step 0: add user message
            if user_message is not None:

                # 对 user_message 类型一个校验
                if isinstance(user_message, RecordMessage):
                    user_message_text = user_message.text
                elif isinstance(user_message, str):
                    user_message_text = user_message
                else:
                    raise ValueError(f"Bad type for user_message: {type(user_message)}")

                # 对于用户输入的信息进行格式化，后期可以考用 RecordMessage 类 
                packed_user_message = {"role": "user", "content": user_message_text}

                # Create the associated RecordMessage object (in the database)
                packed_user_message_obj = RecordMessage.dict_to_message(
                    agent_id=self.agent_state.id,
                    user_id=self.agent_state.user_id,
                    model=self.model,
                    openai_message_dict=packed_user_message,
                )
                # 
                self.interface.user_message(user_message_text, msg_obj=packed_user_message_obj)

                input_message_sequence = self.messages + [packed_user_message]
            # Alternatively, the requestor can send an empty user message
            else:
                input_message_sequence = self.messages
                packed_user_message = None

            if len(input_message_sequence) > 1 and input_message_sequence[-1]["role"] != "user":
                printd(f"{CLI_WARNING_PREFIX}Attempting to run ChatCompletion without user as the last message in the queue")

            # Step 1: send the conversation and available functions to Local LLM
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

            # if is_context_overflow_error(e):
            #     # A separate API call to run a summarizer
            #     self.summarize_messages_inplace()

            #     # Try step again
            #     return self.step(user_message, first_message=first_message, return_dicts=return_dicts)
            # else:
            #     printd(f"step() failed with an unrecognized exception: '{str(e)}'")
            #     raise e

    def heartbeat_is_paused(self):
        """Check if there's a requested pause on timed heartbeats"""

        # Check if the pause has been initiated
        if self.pause_heartbeats_start is None:
            return False

        # Check if it's been more than pause_heartbeats_minutes since pause_heartbeats_start
        elapsed_time = get_utc_time() - self.pause_heartbeats_start
        return elapsed_time.total_seconds() < self.pause_heartbeats_minutes * 60

    def rebuild_memory(self):
        """Rebuilds the system message with the latest memory object"""
        curr_system_message = self.messages[0]  # this is the system + memory bank, not just the system prompt
        new_system_message = initialize_message_sequence(
            self.model,
            self.system,
            self.memory,
            archival_memory=self.persistence_manager.archival_memory,
            recall_memory=self.persistence_manager.recall_memory,
        )[0]

        diff = united_diff(curr_system_message["content"], new_system_message["content"])
        printd(f"Rebuilding system with new memory...\nDiff:\n{diff}")

        # Swap the system message out
        self._swap_system_message(
            RecordMessage.dict_to_message(
                agent_id=self.agent_state.id, user_id=self.agent_state.user_id, model=self.model, openai_message_dict=new_system_message
            )
        )

    # def to_agent_state(self) -> AgentState:
    #    # The state may have change since the last time we wrote it
    #    updated_state = {
    #        "persona": self.memory.persona,
    #        "human": self.memory.human,
    #        "system": self.system,
    #        "functions": self.functions,
    #        "messages": [str(msg.id) for msg in self._messages],
    #    }

    #    agent_state = AgentState(
    #        name=self.agent_state.name,
    #        user_id=self.agent_state.user_id,
    #        persona=self.agent_state.persona,
    #        human=self.agent_state.human,
    #        llm_config=self.agent_state.llm_config,
    #        embedding_config=self.agent_state.embedding_config,
    #        preset=self.agent_state.preset,
    #        id=self.agent_state.id,
    #        created_at=self.agent_state.created_at,
    #        state=updated_state,
    #    )

    #    return agent_state

    def add_function(self, function_name: str) -> str:
        if function_name in self.functions_python.keys():
            msg = f"Function {function_name} already loaded"
            printd(msg)
            return msg

        available_functions = load_all_function_sets()
        if function_name not in available_functions.keys():
            raise ValueError(f"Function {function_name} not found in function library")

        self.functions.append(available_functions[function_name]["json_schema"])
        self.functions_python[function_name] = available_functions[function_name]["python_function"]

        msg = f"Added function {function_name}"
        # self.save()
        self.update_state()
        printd(msg)
        return msg

    def remove_function(self, function_name: str) -> str:
        if function_name not in self.functions_python.keys():
            msg = f"Function {function_name} not loaded, ignoring"
            printd(msg)
            return msg

        # only allow removal of user defined functions
        user_func_path = Path(USER_FUNCTIONS_DIR)
        func_path = Path(inspect.getfile(self.functions_python[function_name]))
        is_subpath = func_path.resolve().parts[: len(user_func_path.resolve().parts)] == user_func_path.resolve().parts

        if not is_subpath:
            raise ValueError(f"Function {function_name} is not user defined and cannot be removed")

        self.functions = [f_schema for f_schema in self.functions if f_schema["name"] != function_name]
        self.functions_python.pop(function_name)

        msg = f"Removed function {function_name}"
        # self.save()
        self.update_state()
        printd(msg)
        return msg

    # def save(self):
    #    """Save agent state locally"""

    #    new_agent_state = self.to_agent_state()

    #    # without this, even after Agent.__init__, agent.config.state["messages"] will be None
    #    self.agent_state = new_agent_state

    #    # Check if we need to create the agent
    #    if not self.ms.get_agent(agent_id=new_agent_state.id, user_id=new_agent_state.user_id, agent_name=new_agent_state.name):
    #        # print(f"Agent.save {new_agent_state.id} :: agent does not exist, creating...")
    #        self.ms.create_agent(agent=new_agent_state)
    #    # Otherwise, we should update the agent
    #    else:
    #        # print(f"Agent.save {new_agent_state.id} :: agent already exists, updating...")
    #        print(f"Agent.save {new_agent_state.id} :: preupdate:\n\tmessages={new_agent_state.state['messages']}")
    #        self.ms.update_agent(agent=new_agent_state)

    def update_state(self) -> AgentState:
        updated_state = {
            "persona": self.memory.persona,
            "human": self.memory.human,
            "system": self.system,
            "functions": self.functions,
            "messages": [str(msg.id) for msg in self._messages],
        }

        self.agent_state = AgentState(
            name=self.agent_state.name,
            user_id=self.agent_state.user_id,
            persona=self.agent_state.persona,
            human=self.agent_state.human,
            llm_config=self.agent_state.llm_config,
            embedding_config=self.agent_state.embedding_config,
            preset=self.agent_state.preset,
            id=self.agent_state.id,
            created_at=self.agent_state.created_at,
            state=updated_state,
        )
        return self.agent_state

    def migrate_embedding(self, embedding_config: EmbeddingConfig):
        """Migrate the agent to a new embedding"""
        # TODO: archival memory

        # TODO: recall memory
        raise NotImplementedError()

    
        """Attach data with name `source_name` to the agent from source_connector."""
        # TODO: eventually, adding a data source should just give access to the retriever the source table, rather than modifying archival memory

        filters = {"user_id": self.agent_state.user_id, "data_source": source_name}
        size = source_connector.size(filters)
        # typer.secho(f"Ingesting {size} passages into {agent.name}", fg=typer.colors.GREEN)
        page_size = 100
        generator = source_connector.get_all_paginated(filters=filters, page_size=page_size)  # yields List[Passage]
        all_passages = []
        for i in tqdm(range(0, size, page_size)):
            passages = next(generator)

            # need to associated passage with agent (for filtering)
            for passage in passages:
                assert isinstance(passage, Passage), f"Generate yielded bad non-Passage type: {type(passage)}"
                passage.agent_id = self.agent_state.id

                # regenerate passage ID (avoid duplicates)
                passage.id = create_uuid_from_string(f"{source_name}_{str(passage.agent_id)}_{passage.text}")

            # insert into agent archival memory
            self.persistence_manager.archival_memory.storage.insert_many(passages)
            all_passages += passages

        assert size == len(all_passages), f"Expected {size} passages, but only got {len(all_passages)}"

        # save destination storage
        self.persistence_manager.archival_memory.storage.save()

        # attach to agent
        source = ms.get_source(source_name=source_name, user_id=self.agent_state.user_id)
        assert source is not None, f"source does not exist for source_name={source_name}, user_id={self.agent_state.user_id}"
        source_id = source.id
        ms.attach_source(agent_id=self.agent_state.id, source_id=source_id, user_id=self.agent_state.user_id)

        total_agent_passages = self.persistence_manager.archival_memory.storage.size()

        printd(
            f"Attached data source {source_name} to agent {self.agent_state.name}, consisting of {len(all_passages)}. Agent now has {total_agent_passages} embeddings in archival memory.",
        )
if __name__ == "__main__":
    agent = Agent()
    agent.step()