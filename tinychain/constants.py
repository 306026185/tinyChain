import os

VARIALBE_EXTRACT_PATTERN = r"\{(\w+)\}"

# 
TINYCHAIN_DIR = os.path.join("D:\\matthew",".tinychain")

CORE_MEMORY_PERSONA_CHAR_LIMIT = 2000
CORE_MEMORY_HUMAN_CHAR_LIMIT = 2000

DEFAULT_PERSONA = "tinychain_starter"
DEFAULT_HUMAN = "zidea"
DEFAULT_PRESET = "tinychain_chat"

MAX_EMBEDDING_DIM = 4096 

TOOL_CALL_ID_MAX_LEN = 29

FIRST_MESSAGE_ATTEMPTS = 10

INITIAL_BOOT_MESSAGE = "Boot sequence complete. Persona activated."
INITIAL_BOOT_MESSAGE_SEND_MESSAGE_THOUGHT = "Bootup sequence complete. Persona activated. Testing messaging functionality."
STARTUP_QUOTES = [
    "I think, therefore I am.",
    "All those moments will be lost in time, like tears in rain.",
    "More human than human is our motto.",
]
INITIAL_BOOT_MESSAGE_SEND_MESSAGE_FIRST_MSG = STARTUP_QUOTES[2]


JSON_LOADS_STRICT = False
MESSAGE_SUMMARY_WARNING_FRAC = 0.75
MESSAGE_SUMMARY_TRUNC_TOKEN_FRAC = 0.75
MESSAGE_SUMMARY_TRUNC_KEEP_N_LAST = 3
LLM_MAX_TOKENS = {
    "DEFAULT":8192,
    "ollama":8192
}
CLI_WARNING_PREFIX = "Warning: "
JSON_ENSURE_ASCII = False

FUNCTION_PARAM_NAME_REQ_HEARTBEAT = "request_heartbeat"
FUNCTION_PARAM_TYPE_REQ_HEARTBEAT = "boolean"
FUNCTION_PARAM_DESCRIPTION_REQ_HEARTBEAT = "Request an immediate heartbeat after function execution. Set to 'true' if you want to send a follow-up message or run a follow-up function."

MESSAGE_CHATGPT_FUNCTION_MODEL = "llama3"
MESSAGE_CHATGPT_FUNCTION_SYSTEM_MESSAGE = "You are a helpful assistant. Keep your responses short and concise."
RETRIEVAL_QUERY_DEFAULT_PAGE_SIZE = 5
MAX_PAUSE_HEARTBEATS = 360