import os
import uuid
from typing import Any, List, Optional

import ollama

import numpy as np

from tinychain.data_type import EmbeddingConfig


def embedding_model():
    def inner_func():
        reponse = ollama.embeddings(
            model='mxbai-embed-large',
            prompt='Llamas are members of the camelid family',
        )
        return reponse
    
    return inner_func
