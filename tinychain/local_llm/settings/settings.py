

from tinychain.constants import TINYCHAIN_DIR

from tinychain.local_llm.settings.simple import settings as simple_settings
from tinychain.utils import printd


SETTINGS_FOLDER_NAME = "settings"

def get_completions_settings():
    printd(f"Loading default settings from 'simple settings'")
    settings = simple_settings

    return settings