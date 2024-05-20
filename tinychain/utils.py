import os

import json
import re

from typing import Tuple
from typing import get_type_hints

import glob
import yaml


import inspect
import tiktoken

from tinychain.message.messages import BaseMessage
from tinychain.constants import (
    VARIALBE_EXTRACT_PATTERN,
    TINYCHAIN_DIR,
    CORE_MEMORY_PERSONA_CHAR_LIMIT,
    CORE_MEMORY_HUMAN_CHAR_LIMIT
    )
from tinychain.model.chat_completion_response import ChatCompletionResponse

from rich.console import Console

DEBUG = True

console = Console()

def printd(*args,**kwargs):
    if DEBUG:
         console.print(*args,**kwargs)


# 计算 token 数量
def count_tokens(s: str, model: str = "gpt-4") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(s))

def get_variables(template):
    matches = re.findall(VARIALBE_EXTRACT_PATTERN, template)
    input_variables = []
    if len(matches) > 0:
        for m in matches:
            input_variables.append(m)

    return input_variables

def get_type_name(t):
    name = str(t)
    if "list" in name or "dict" in name:
        return name
    else:
        return t.__name__
    
def function_to_json(func):
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)

    function_info = {
        "name": func.__name__,
        "description": func.__doc__,
        "parameters": {"type": "object", "properties": {}},
        "returns": type_hints.get("return", "void").__name__,
    }

    for name, _ in signature.parameters.items():
        param_type = get_type_name(type_hints.get(name, type(None)))
        function_info["parameters"]["properties"][name] = {"type": param_type}

    return json.dumps(function_info, indent=2)


def check_messages_type(messages):
    if all(isinstance(msg, Tuple) and len(msg) == 2 and isinstance(msg[0], str) and isinstance(msg[1], str) for msg in messages):
        return "List[Tuple[str, str]]"
    elif all(isinstance(msg, BaseMessage) for msg in messages):
        return "List[BaseMessage]"
    else:
        return "Unknown or mixed type"
    
def list_persona_files():
    """List all personas files"""

    current_path = os.getcwd()
    # 获取当前项目路径
    defaults_dir = os.path.join(current_path,"tinychain","personas", "examples")
    user_dir = os.path.join(TINYCHAIN_DIR, "personas")

    memgpt_defaults = os.listdir(defaults_dir)
    memgpt_defaults = [os.path.join(defaults_dir, f) for f in memgpt_defaults if f.endswith(".txt")]

    if os.path.exists(user_dir):
        user_added = os.listdir(user_dir)
        user_added = [os.path.join(user_dir, f) for f in user_added]
    else:
        user_added = []
    return memgpt_defaults + user_added
    
def get_persona_text(name: str, enforce_limit=True):
    for file_path in list_persona_files():
        file = os.path.basename(file_path)
        if f"{name}.txt" == file or name == file:
            persona_text = open(file_path, "r").read().strip()
            if enforce_limit and len(persona_text) > CORE_MEMORY_PERSONA_CHAR_LIMIT:
                raise ValueError(
                    f"Contents of {name}.txt is over the character limit ({len(persona_text)} > {CORE_MEMORY_PERSONA_CHAR_LIMIT})"
                )
             # printd(open(file_path, "r").read().strip())
            return persona_text

    raise ValueError(f"Persona {name}.txt not found")

def list_human_files():
    """List all humans files"""

    current_path = os.getcwd()

    defaults_dir = os.path.join(current_path,"tinychain","humans", "examples")
    user_dir = os.path.join(TINYCHAIN_DIR, "humans")

    tinychain_defaults = os.listdir(defaults_dir)
    tinychain_defaults = [os.path.join(defaults_dir, f) for f in tinychain_defaults 
    if f.endswith(".txt")]

    if os.path.exists(user_dir):
        user_added = os.listdir(user_dir)
        user_added = [os.path.join(user_dir, f) for f in user_added]
    else:
        user_added = []

    printd(tinychain_defaults + user_added)
    return tinychain_defaults + user_added

def get_human_text(name: str):
    for file_path in list_human_files():
        file = os.path.basename(file_path)
        if f"{name}.txt" == file or name == file:
           
            # printd(open(file_path, "r").read().strip())
            return open(file_path, "r").read().strip()
        
def load_yaml_file(file_path):
    """
    Load a YAML file and return the data.

    :param file_path: Path to the YAML file.
    :return: Data from the YAML file.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def load_all_presets():
    """Load all the preset configs in the examples directory"""

    ## Load the examples
    # Get the directory in which the script is located
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # Construct the path pattern
    printd(f"{script_directory=}")
    example_path_pattern = os.path.join(script_directory, "examples", "*.yaml")
    
    printd(f"{example_path_pattern=}")

    # Listing all YAML files
    example_yaml_files = glob.glob(example_path_pattern)
    console.print(example_yaml_files)

    ## Load the user-provided presets
    # ~/tinychain/presets/*.yaml
    user_presets_dir = os.path.join(TINYCHAIN_DIR, "presets")
    # Create directory if it doesn't exist
    if not os.path.exists(user_presets_dir):
        os.makedirs(user_presets_dir)
    # Construct the path pattern

    console.print(":file:")
    user_path_pattern = os.path.join(user_presets_dir, "*.yaml")
    console.print(user_path_pattern)
    # Listing all YAML files
    user_yaml_files = glob.glob(user_path_pattern)
    console.print(user_yaml_files)

    # Pull from both examplesa and user-provided
    all_yaml_files = example_yaml_files + user_yaml_files
    printd(f"{all_yaml_files=}")
    # Loading and creating a mapping from file name to YAML data
    all_yaml_data = {}
    for file_path in all_yaml_files:
        # Extracting the base file name without the '.yaml' extension
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        data = load_yaml_file(file_path)
        all_yaml_data[base_name] = data

    console.print(all_yaml_data)
    exit(0)
    return all_yaml_data


def verify_first_message_correctness(
    response: ChatCompletionResponse, require_send_message: bool = True, require_monologue: bool = False
) -> bool:
    """Can be used to enforce that the first message always uses send_message"""
    response_message = response.choices[0].message

    # First message should be a call to send_message with a non-empty content
    if (hasattr(response_message, "function_call") and response_message.function_call is not None) and (
        hasattr(response_message, "tool_calls") and response_message.tool_calls is not None
    ):
        printd(f"First message includes both function call AND tool call: {response_message}")
        return False
    elif hasattr(response_message, "function_call") and response_message.function_call is not None:
        function_call = response_message.function_call
    elif hasattr(response_message, "tool_calls") and response_message.tool_calls is not None:
        function_call = response_message.tool_calls[0].function
    else:
        printd(f"First message didn't include function call: {response_message}")
        return False

    function_name = function_call.name if function_call is not None else ""
    if require_send_message and function_name != "send_message" and function_name != "archival_memory_search":
        printd(f"First message function call wasn't send_message or archival_memory_search: {response_message}")
        return False

    if require_monologue and (not response_message.content or response_message.content is None or response_message.content == ""):
        printd(f"First message missing internal monologue: {response_message}")
        return False

    if response_message.content:
        ### Extras
        monologue = response_message.content

        def contains_special_characters(s):
            special_characters = '(){}[]"'
            return any(char in s for char in special_characters)

        if contains_special_characters(monologue):
            printd(f"First message internal monologue contained special characters: {response_message}")
            return False
        # if 'functions' in monologue or 'send_message' in monologue or 'inner thought' in monologue.lower():
        if "functions" in monologue or "send_message" in monologue:
            # Sometimes the syntax won't be correct and internal syntax will leak into message.context
            printd(f"First message internal monologue contained reserved words: {response_message}")
            return False

    return True
if __name__ == "__main__":
    get_human_text("zidea.txt")
    get_persona_text("tinychain_starter")


    load_all_presets()