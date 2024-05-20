import os
import uuid

from typing import List


from tinychain.data_type import Preset
from tinychain.utils import printd,get_persona_text,get_human_text,load_all_presets
from tinychain.constants import DEFAULT_PERSONA,DEFAULT_HUMAN,DEFAULT_PRESET
from tinychain.local_llm.chat_completion_proxy import SUMMARIZE_SYSTEM_MESSAGE
from tinychain.functions.functions import load_all_function_sets



available_presets = load_all_presets()


def generate_functions_json(preset_functions: List[str]):
    """
    Generate JSON schema for the functions based on what is locally available.

    TODO: store function definitions in the DB, instead of locally
    """
    # Available functions is a mapping from:
    # function_name -> {
    #   json_schema: schema
    #   python_function: function
    # }
    available_functions = load_all_function_sets()

    # Filter down the function set based on what the preset requested
    preset_function_set = {}
    for f_name in preset_functions:
        if f_name not in available_functions:
            raise ValueError(f"Function '{f_name}' was specified in preset, but is not in function library:\n{available_functions.keys()}")
        preset_function_set[f_name] = available_functions[f_name]
    assert len(preset_functions) == len(preset_function_set)
    preset_function_set_schemas = [f_dict["json_schema"] for f_name, f_dict in preset_function_set.items()]
    printd(f"Available functions:\n", list(preset_function_set.keys()))
    return preset_function_set_schemas


def get_default_presets(user_id: uuid.UUID):
    """Add the default presets to the metadata store"""

    preset_config = available_presets['default_preset']
    # printd(preset_config)
    preset_system_prompt = preset_config["system_prompt"]

    preset_function_set_names = preset_config["functions"]

    # printd(preset_function_set_names)

    functions_schema = generate_functions_json(preset_function_set_names)

    # printd("[bold]functions_schema[/]")
    # printd(functions_schema)
    # printd("--"*50)
    # add default presets
    preset = Preset(
        user_id=user_id,
        name=DEFAULT_PRESET,
        system=SUMMARIZE_SYSTEM_MESSAGE,
        persona=get_persona_text(DEFAULT_PERSONA),
        persona_name=DEFAULT_PERSONA,
        human=get_human_text(DEFAULT_HUMAN),
        human_name=DEFAULT_HUMAN,
        functions_schema=functions_schema,
    )

    return preset


if __name__ == "__main__":
    available_presets = load_all_presets()
    # printd(available_presets)

    get_default_presets(user_id=uuid.uuid4())