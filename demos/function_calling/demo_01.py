import json
import inspect

from typing import get_type_hints

from rich import print_json

from rich.console import Console

console = Console()

def add(a:int,b:int)->int:
    """useful for cacluate the sum of a and b"""
    return a + b

def outputParser(response:str):
    try:
        res = response.strip().replace("\n","").replace("\\","")
        console.print_json(res)
        return res
    except Exception:
        console.print(f"Unable to decode JSON {response}")


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

def main():
    pass

if __name__ == "__main__":
    function_to_json(add)
    main()