import json
import re

from typing import Tuple
from typing import get_type_hints

from rich.console import Console
import inspect


from tinychain.message.messages import BaseMessage
from tinychain.constants import VARIALBE_EXTRACT_PATTERN

console = Console()

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

    console.log(func.__doc__)
    console.print(type_hints)

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