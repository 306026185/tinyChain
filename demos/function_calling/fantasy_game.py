import json
import instructor

from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List,Optional
from typing_extensions import Annotated

import concurrent.futures
from termcolor import colored
import random
import os