import os
import random
import json
import re
import hashlib
import difflib
import uuid
from datetime import datetime, timedelta, timezone
import pytz
import inspect
import tiktoken
import glob
import yaml

import demjson3 as demjson
from functools import wraps

from typing import Tuple
from typing import get_type_hints






from tinychain.message.messages import BaseMessage
from tinychain.constants import (
    JSON_ENSURE_ASCII,
    VARIALBE_EXTRACT_PATTERN,
    TINYCHAIN_DIR,
    CORE_MEMORY_PERSONA_CHAR_LIMIT,
    CORE_MEMORY_HUMAN_CHAR_LIMIT,
    CLI_WARNING_PREFIX,
    FUNCTION_RETURN_CHAR_LIMIT,
    
    TOOL_CALL_ID_MAX_LEN
    )
from tinychain.model.chat_completion_response import ChatCompletionResponse

from rich.console import Console

DEBUG = True

console = Console()

ADJECTIVE_BANK = [
    "beautiful",
    "gentle",
    "angry",
    "vivacious",
    "grumpy",
    "luxurious",
    "fierce",
    "delicate",
    "fluffy",
    "radiant",
    "elated",
    "magnificent",
    "sassy",
    "ecstatic",
    "lustrous",
    "gleaming",
    "sorrowful",
    "majestic",
    "proud",
    "dynamic",
    "energetic",
    "mysterious",
    "loyal",
    "brave",
    "decisive",
    "frosty",
    "cheerful",
    "adorable",
    "melancholy",
    "vibrant",
    "elegant",
    "gracious",
    "inquisitive",
    "opulent",
    "peaceful",
    "rebellious",
    "scintillating",
    "dazzling",
    "whimsical",
    "impeccable",
    "meticulous",
    "resilient",
    "charming",
    "vivacious",
    "creative",
    "intuitive",
    "compassionate",
    "innovative",
    "enthusiastic",
    "tremendous",
    "effervescent",
    "tenacious",
    "fearless",
    "sophisticated",
    "witty",
    "optimistic",
    "exquisite",
    "sincere",
    "generous",
    "kindhearted",
    "serene",
    "amiable",
    "adventurous",
    "bountiful",
    "courageous",
    "diligent",
    "exotic",
    "grateful",
    "harmonious",
    "imaginative",
    "jubilant",
    "keen",
    "luminous",
    "nurturing",
    "outgoing",
    "passionate",
    "quaint",
    "resourceful",
    "sturdy",
    "tactful",
    "unassuming",
    "versatile",
    "wondrous",
    "youthful",
    "zealous",
    "ardent",
    "benevolent",
    "capricious",
    "dedicated",
    "empathetic",
    "fabulous",
    "gregarious",
    "humble",
    "intriguing",
    "jovial",
    "kind",
    "lovable",
    "mindful",
    "noble",
    "original",
    "pleasant",
    "quixotic",
    "reliable",
    "spirited",
    "tranquil",
    "unique",
    "venerable",
    "warmhearted",
    "xenodochial",
    "yearning",
    "zesty",
    "amusing",
    "blissful",
    "calm",
    "daring",
    "enthusiastic",
    "faithful",
    "graceful",
    "honest",
    "incredible",
    "joyful",
    "kind",
    "lovely",
    "merry",
    "noble",
    "optimistic",
    "peaceful",
    "quirky",
    "respectful",
    "sweet",
    "trustworthy",
    "understanding",
    "vibrant",
    "witty",
    "xenial",
    "youthful",
    "zealous",
    "ambitious",
    "brilliant",
    "careful",
    "devoted",
    "energetic",
    "friendly",
    "glorious",
    "humorous",
    "intelligent",
    "jovial",
    "knowledgeable",
    "loyal",
    "modest",
    "nice",
    "obedient",
    "patient",
    "quiet",
    "resilient",
    "selfless",
    "tolerant",
    "unique",
    "versatile",
    "warm",
    "xerothermic",
    "yielding",
    "zestful",
    "amazing",
    "bold",
    "charming",
    "determined",
    "exciting",
    "funny",
    "happy",
    "imaginative",
    "jolly",
    "keen",
    "loving",
    "magnificent",
    "nifty",
    "outstanding",
    "polite",
    "quick",
    "reliable",
    "sincere",
    "thoughtful",
    "unusual",
    "valuable",
    "wonderful",
    "xenodochial",
    "zealful",
    "admirable",
    "bright",
    "clever",
    "dedicated",
    "extraordinary",
    "generous",
    "hardworking",
    "inspiring",
    "jubilant",
    "kindhearted",
    "lively",
    "miraculous",
    "neat",
    "openminded",
    "passionate",
    "remarkable",
    "stunning",
    "truthful",
    "upbeat",
    "vivacious",
    "welcoming",
    "yare",
    "zealous",
]

NOUN_BANK = [
    "lizard",
    "firefighter",
    "banana",
    "castle",
    "dolphin",
    "elephant",
    "forest",
    "giraffe",
    "harbor",
    "iceberg",
    "jewelry",
    "kangaroo",
    "library",
    "mountain",
    "notebook",
    "orchard",
    "penguin",
    "quilt",
    "rainbow",
    "squirrel",
    "teapot",
    "umbrella",
    "volcano",
    "waterfall",
    "xylophone",
    "yacht",
    "zebra",
    "apple",
    "butterfly",
    "caterpillar",
    "dragonfly",
    "elephant",
    "flamingo",
    "gorilla",
    "hippopotamus",
    "iguana",
    "jellyfish",
    "koala",
    "lemur",
    "mongoose",
    "nighthawk",
    "octopus",
    "panda",
    "quokka",
    "rhinoceros",
    "salamander",
    "tortoise",
    "unicorn",
    "vulture",
    "walrus",
    "xenopus",
    "yak",
    "zebu",
    "asteroid",
    "balloon",
    "compass",
    "dinosaur",
    "eagle",
    "firefly",
    "galaxy",
    "hedgehog",
    "island",
    "jaguar",
    "kettle",
    "lion",
    "mammoth",
    "nucleus",
    "owl",
    "pumpkin",
    "quasar",
    "reindeer",
    "snail",
    "tiger",
    "universe",
    "vampire",
    "wombat",
    "xerus",
    "yellowhammer",
    "zeppelin",
    "alligator",
    "buffalo",
    "cactus",
    "donkey",
    "emerald",
    "falcon",
    "gazelle",
    "hamster",
    "icicle",
    "jackal",
    "kitten",
    "leopard",
    "mushroom",
    "narwhal",
    "opossum",
    "peacock",
    "quail",
    "rabbit",
    "scorpion",
    "toucan",
    "urchin",
    "viper",
    "wolf",
    "xray",
    "yucca",
    "zebu",
    "acorn",
    "biscuit",
    "cupcake",
    "daisy",
    "eyeglasses",
    "frisbee",
    "goblin",
    "hamburger",
    "icicle",
    "jackfruit",
    "kaleidoscope",
    "lighthouse",
    "marshmallow",
    "nectarine",
    "obelisk",
    "pancake",
    "quicksand",
    "raspberry",
    "spinach",
    "truffle",
    "umbrella",
    "volleyball",
    "walnut",
    "xylophonist",
    "yogurt",
    "zucchini",
    "asterisk",
    "blackberry",
    "chimpanzee",
    "dumpling",
    "espresso",
    "fireplace",
    "gnome",
    "hedgehog",
    "illustration",
    "jackhammer",
    "kumquat",
    "lemongrass",
    "mandolin",
    "nugget",
    "ostrich",
    "parakeet",
    "quiche",
    "racquet",
    "seashell",
    "tadpole",
    "unicorn",
    "vaccination",
    "wolverine",
    "xenophobia",
    "yam",
    "zeppelin",
    "accordion",
    "broccoli",
    "carousel",
    "daffodil",
    "eggplant",
    "flamingo",
    "grapefruit",
    "harpsichord",
    "impression",
    "jackrabbit",
    "kitten",
    "llama",
    "mandarin",
    "nachos",
    "obelisk",
    "papaya",
    "quokka",
    "rooster",
    "sunflower",
    "turnip",
    "ukulele",
    "viper",
    "waffle",
    "xylograph",
    "yeti",
    "zephyr",
    "abacus",
    "blueberry",
    "crocodile",
    "dandelion",
    "echidna",
    "fig",
    "giraffe",
    "hamster",
    "iguana",
    "jackal",
    "kiwi",
    "lobster",
    "marmot",
    "noodle",
    "octopus",
    "platypus",
    "quail",
    "raccoon",
    "starfish",
    "tulip",
    "urchin",
    "vampire",
    "walrus",
    "xylophone",
    "yak",
    "zebra",
]

def get_local_time_military():
    # Get the current time in UTC
    current_time_utc = datetime.now(pytz.utc)

    # Convert to San Francisco's time zone (PST/PDT)
    sf_time_zone = pytz.timezone("Asia/Shanghai")
    local_time = current_time_utc.astimezone(sf_time_zone)

    # You may format it as you desire
    formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")

    return formatted_time

def get_utc_time() -> datetime:
    """Get the current UTC time"""
    # return datetime.now(pytz.utc)
    return datetime.now(timezone.utc)

def is_utc_datetime(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) == timedelta(0)


def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %I:%M:%S %p %Z%z")


def parse_json(string) -> dict:
    """Parse JSON string into JSON with both json and demjson"""
    result = None
    try:
        result = json.loads(string, strict=JSON_LOADS_STRICT)
        return result
    except Exception as e:
        print(f"Error parsing json with json package: {e}")

    try:
        result = demjson.decode(string)
        return result
    except demjson.JSONDecodeError as e:
        print(f"Error parsing json with demjson package: {e}")
        raise e

def get_schema_diff(schema_a, schema_b):
    # Assuming f_schema and linked_function['json_schema'] are your JSON schemas
    f_schema_json = json.dumps(schema_a, indent=2, ensure_ascii=JSON_ENSURE_ASCII)
    linked_function_json = json.dumps(schema_b, indent=2, ensure_ascii=JSON_ENSURE_ASCII)

    # Compute the difference using difflib
    difference = list(difflib.ndiff(f_schema_json.splitlines(keepends=True), linked_function_json.splitlines(keepends=True)))

    # Filter out lines that don't represent changes
    difference = [line for line in difference if line.startswith("+ ") or line.startswith("- ")]

    return "".join(difference)

def get_tool_call_id() -> str:
    return str(uuid.uuid4())[:TOOL_CALL_ID_MAX_LEN]

def printd(*args,**kwargs):
    if DEBUG:
         console.print(*args,**kwargs)

def united_diff(str1, str2):
    lines1 = str1.splitlines(True)
    lines2 = str2.splitlines(True)
    diff = difflib.unified_diff(lines1, lines2)
    return "".join(diff)

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

def validate_function_response(function_response_string: any, strict: bool = False, truncate: bool = True) -> str:
    """Check to make sure that a function used by MemGPT returned a valid response

    Responses need to be strings (or None) that fall under a certain text count limit.
    """
    if not isinstance(function_response_string, str):
        # Soft correction for a few basic types

        if function_response_string is None:
            # function_response_string = "Empty (no function output)"
            function_response_string = "None"  # backcompat

        elif isinstance(function_response_string, dict):
            if strict:
                # TODO add better error message
                raise ValueError(function_response_string)

            # Allow dict through since it will be cast to json.dumps()
            try:
                # TODO find a better way to do this that won't result in double escapes
                function_response_string = json.dumps(function_response_string, ensure_ascii=JSON_ENSURE_ASCII)
            except:
                raise ValueError(function_response_string)

        else:
            if strict:
                # TODO add better error message
                raise ValueError(function_response_string)

            # Try to convert to a string, but throw a warning to alert the user
            try:
                function_response_string = str(function_response_string)
            except:
                raise ValueError(function_response_string)

    # Now check the length and make sure it doesn't go over the limit
    # TODO we should change this to a max token limit that's variable based on tokens remaining (or context-window)
    if truncate and len(function_response_string) > FUNCTION_RETURN_CHAR_LIMIT:
        print(
            f"{CLI_WARNING_PREFIX}function return was over limit ({len(function_response_string)} > {FUNCTION_RETURN_CHAR_LIMIT}) and was truncated"
        )
        function_response_string = f"{function_response_string[:FUNCTION_RETURN_CHAR_LIMIT]}... [NOTE: function output was truncated since it exceeded the character limit ({len(function_response_string)} > {FUNCTION_RETURN_CHAR_LIMIT})]"

    return function_response_string


def create_random_username() -> str:
    """Generate a random username by combining an adjective and a noun."""
    adjective = random.choice(ADJECTIVE_BANK).capitalize()
    noun = random.choice(NOUN_BANK).capitalize()
    return adjective + noun

def create_uuid_from_string(val: str):
    """
    Generate consistent UUID from a string
    from: https://samos-it.com/posts/python-create-uuid-from-random-string-of-words.html
    """
    hex_string = hashlib.md5(val.encode("UTF-8")).hexdigest()
    return uuid.UUID(hex=hex_string)

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
    example_path_pattern = os.path.join(script_directory, "examples", "*.yaml")
    

    # Listing all YAML files
    example_yaml_files = glob.glob(example_path_pattern)

    ## Load the user-provided presets
    # ~/tinychain/presets/*.yaml
    user_presets_dir = os.path.join(TINYCHAIN_DIR, "presets")
    # Create directory if it doesn't exist
    if not os.path.exists(user_presets_dir):
        os.makedirs(user_presets_dir)
    # Construct the path pattern

    user_path_pattern = os.path.join(user_presets_dir, "*.yaml")
    # Listing all YAML files
    user_yaml_files = glob.glob(user_path_pattern)

    # Pull from both examplesa and user-provided
    all_yaml_files = example_yaml_files + user_yaml_files
    # Loading and creating a mapping from file name to YAML data
    all_yaml_data = {}
    for file_path in all_yaml_files:
        # Extracting the base file name without the '.yaml' extension
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        data = load_yaml_file(file_path)
        all_yaml_data[base_name] = data

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