import os
import sys
import warnings

import importlib
import inspect

from types import ModuleType

from tinychain.constants import CLI_WARNING_PREFIX, TINYCHAIN_DIR
from tinychain.functions.schema_generator import generate_schema

from tinychain.utils import printd

USER_FUNCTIONS_DIR = os.path.join(TINYCHAIN_DIR, "functions")

sys.path.append(USER_FUNCTIONS_DIR)

def load_function_set(module: ModuleType) -> dict:
    """Load the functions and generate schema for them, given a module object"""
    function_dict = {}

    for attr_name in dir(module):
        # Get the attribute
        attr = getattr(module, attr_name)

        # Check if it's a callable function and not a built-in or special method
        if inspect.isfunction(attr) and attr.__module__ == module.__name__:
            if attr_name in function_dict:
                raise ValueError(f"Found a duplicate of function name '{attr_name}'")

           
            generated_schema = generate_schema(attr)
            function_dict[attr_name] = {
                "python_function": attr,
                "json_schema": generated_schema,
            }

    if len(function_dict) == 0:
        raise ValueError(f"No functions found in module {module}")
    return function_dict

def load_all_function_sets(
        merge: bool = True, 
        ignore_duplicates: bool = True) -> dict:

    # functions/examples/*.py
    scripts_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
    
    # '/home/user/tinyChain/tinychain/functions'
    printd(f"{scripts_dir=}")
    
    function_sets_dir = os.path.join(scripts_dir, "function_sets")  # Path to the function_sets directory
    # List all .py files in the directory (excluding __init__.py)

    printd(f"{function_sets_dir=}")
    example_module_files = [f for f in os.listdir(function_sets_dir) if f.endswith(".py") and f != "__init__.py"]
    printd(f"{example_module_files=}")

    # ~/tinychain/functions/*.py
    # create if missing
    if not os.path.exists(USER_FUNCTIONS_DIR):
        os.makedirs(USER_FUNCTIONS_DIR)
    user_module_files = [f for f in os.listdir(USER_FUNCTIONS_DIR) if f.endswith(".py") and f != "__init__.py"]

    # combine them both (pull from both examples and user-provided)
    all_module_files = example_module_files + user_module_files

    # Add user_scripts_dir to sys.path

    # printd(f"{USER_FUNCTIONS_DIR=}")

    if USER_FUNCTIONS_DIR not in sys.path:
        sys.path.append(USER_FUNCTIONS_DIR)

    schemas_and_functions = {}
    for dir_path, module_files in [(function_sets_dir, example_module_files)]:
        for file in module_files:
            tags = []
            module_name = file[:-3]  # Remove '.py' from filename
            if dir_path == USER_FUNCTIONS_DIR:
                # For user scripts, adjust the module name appropriately
                module_full_path = os.path.join(dir_path, file)
                printd(f"Loading user function set from '{module_full_path}'")
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_full_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except ModuleNotFoundError as e:
                    # Handle missing module imports
                    missing_package = str(e).split("'")[1]  # Extract the name of the missing package
                    printd(f"{CLI_WARNING_PREFIX}skipped loading python file '{module_full_path}'!")
                    printd(
                        f"'{file}' imports '{missing_package}', but '{missing_package}' is not installed locally - install python package '{missing_package}' to link functions from '{file}' to MemGPT."
                    )
                    continue
                except SyntaxError as e:
                    # Handle syntax errors in the module
                    printd(f"{CLI_WARNING_PREFIX}skipped loading python file '{file}' due to a syntax error: {e}")
                    continue
                except Exception as e:
                    # Handle other general exceptions
                    printd(f"{CLI_WARNING_PREFIX}skipped loading python file '{file}': {e}")
                    continue
            else:
                # For built-in scripts, use the existing method
                full_module_name = f"tinychain.functions.function_sets.{module_name}"
                tags.append(f"tinychain-{module_name}")
                try:
                    module = importlib.import_module(full_module_name)
                except Exception as e:
                    # Handle other general exceptions
                    printd(f"{CLI_WARNING_PREFIX}skipped loading python module '{full_module_name}': {e}")
                    continue

            try:
                # Load the function set
                function_set = load_function_set(module)
                # Add the metadata tags
                for k, v in function_set.items():
                    # print(function_set)
                    v["tags"] = tags
                schemas_and_functions[module_name] = function_set
                printd(schemas_and_functions)
            except ValueError as e:
                err = f"Error loading function set '{module_name}': {e}"
                printd(err)
                warnings.warn(err)

    if merge:
        # Put all functions from all sets into the same level dict
        merged_functions = {}
        for set_name, function_set in schemas_and_functions.items():
            for function_name, function_info in function_set.items():
                if function_name in merged_functions:
                    err_msg = f"Duplicate function name '{function_name}' found in function set '{set_name}'"
                    if ignore_duplicates:
                        warnings.warn(err_msg, category=UserWarning, stacklevel=2)
                    else:
                        raise ValueError(err_msg)
                else:
                    merged_functions[function_name] = function_info
        return merged_functions
    else:
        # Nested dict where the top level is organized by the function set name
        return schemas_and_functions
    

if __name__ == "__main__":
    print(USER_FUNCTIONS_DIR)