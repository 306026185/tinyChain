import json
import inspect

import requests

from typing import get_type_hints
from rich.console import Console

console = Console()

def function_to_json(func):
    # 获取
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    # (city_name: str) -> float
    # print(signature)

    print(func.__doc__)
    print(func.__name__)

    function_info = {
        "name":func.__name__,
        "description":func.__doc__,
        "parameters":{"type":"object","properties":{}},
        "returns":type_hints.get("return","void").__name__

    }

    for name,_ in signature.parameters.items():
        param_type = get_type_name(type_hints.get(name,type(None)))
        function_info['parameters']['properties'][name] = {"type":param_type}
    
    return json.dumps(function_info,indent=2)

class Weather:
    pass

class Direction:
    pass

def get_weather(city_name:str)->float:
    """useful for get weatcher if user query weather of city"""
    return 15.2

def get_type_name(t):
    name = str(t)
    if "list" in name or "dict" in name:
        return name
    else:
        return t.__name__

def get_weather(city_name:str)->Weather:
    """Get the current weather given a city."""
    # TODO: you must implement this to actually call it later


def get_directions(start:str,destination:str)->Direction: 
    """Get directions from Google Directions API.
    start: start address as a string including zipcode (if any)
    destination: end address as a string including zipcode (if any)"""
functions_prompt = f"""
You have access to the following tools:
{function_to_json(get_weather)}
{function_to_json(get_directions)}

You must follow these instructions:
Always select one or more of the above tools based on the user query
If a tool is found, you must respond in the JSON format matching the following schema:
{{
   "tools": {{
        "tool": "<name of the selected tool>",
        "tool_input": <parameters for the selected tool, matching the tool's JSON schema
   }}
}}
If there are multiple tools required, make sure a list of tools are returned in a JSON array.
If there is no tool that match the user request, you will respond with empty json.
Do not add any additional Notes or Explanations

User Qeury: What's the weather in shenyang
    """

def chat_completion(prompt:str,**kwargs)->dict[str,str]:
    params = {"model":"llama3","prompt":prompt,"stream":False}

    try:
        response = requests.post(
            f"http://localhost:11434/api/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps(params),
            timeout=60
        )
        console.print(response.text)
        return json.loads(response.text)

    except requests.RequestException as err:
        console.print_json({"error":f"{str(err)}"})





"""
获取 func 的描述
name 
description func.__doc__
paramters
returns
"""



def output_parser(rsp):
    return rsp.get("response",rsp).strip().replace("\n","").replace("\\","")

if __name__ == "__main__":

    rsp = chat_completion(functions_prompt)
    console.print(rsp.get("response").strip().replace("\n","").replace("\\",""))
    exit(0)
    processed_rsp = output_parser(rsp)
    console.print_json(processed_rsp)

    res = function_to_json(get_weather)
    console.print_json(res)


    def dosomething(task:dict)->None:
        print("do something ...")

    dosomething_type_hints = get_type_hints(dosomething)
    for name,_ in dosomething_type_hints.items():
        name_str = str(name)
        print(name.__name__)
        print(("dict" in name_str))
    print(dosomething_type_hints)

    def add(a:int,b:int)->int:
        return a + b
    
    add_type_hints = get_type_hints(add)
    # 获取 add 返回值的类型
    print(add_type_hints.get("return","void").__name__)
    

