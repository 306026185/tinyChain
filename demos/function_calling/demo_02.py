import os

import importlib.util
from pathlib import Path


from inspect import signature, Parameter
import functools
import re
from typing import Callable, Dict, List
import logging
logger = logging.getLogger(__name__)

class ToolsRegistry:
    def __init__(self) -> None:
        self.functions_dir = Path(__file__).parent.parent / 'functions'
        self.registry: Dict[str, callable] = {}
        self.schema_registry: Dict[str, Dict] = {}
        self.load_tools()

    def load_tools(self) -> None:
        if not self.functions_dir.exists():

def tool_schema(name: str, description: str, required_params: List[str]):
    def decorator_function(func: Callable) -> Callable:
        if not all(param in signature(func).parameters for param in required_params):
            raise ValueError(f"Missing required parameters in {func.__name__}")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        params = signature(func).parameters
        param_descriptions = parse_doc_str(func)

        serialized_params = {
            param_name: {
                "type": "string",
                "description": param_descriptions.get(param_name, "No description")
            }
            for param_name in required_params
        }

        wrapper.schema = {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": serialized_params,
                "required": required_params
            }
        }
        return wrapper
    return decorator_function

def parse_doc_str(func: Callable) -> Dict[str, str]:
    """
    Parses the docstring of a function and returns a dict with parameter descriptions.
    """
    doc = func.__doc__
    if not doc:
        return {}

    param_re = re.compile(r':param\s+(\w+):\s*(.*)')
    param_descriptions = {}

    for line in doc.split('\n'):
        match = param_re.match(line.strip())
        if match:
            param_name, param_desc = match.groups()
            param_descriptions[param_name] = param_desc

    return param_descriptions