from urllib.parse import urljoin
import requests

from rich.console import Console

from tinychain.utils import printd,count_tokens
from tinychain.local_llm.settings.settings import get_completions_settings

"""
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Why is the sky blue?"
}'
"""

console = Console()

OLLAMA_API_BASE_URL = "/api/generate"

def get_ollama_completion(endpoint:str,
                          model_name:str,
                          prompt:str,
                          context_window:int=8192):

    # 计算 token 数量
    prompt_tokens = count_tokens(prompt)

    if prompt_tokens > context_window:
        raise Exception(f"Request exceeds maximum context length ({prompt_tokens} > {context_window} tokens)")
    
    if model_name is None:
        raise ValueError("you should give model name")
    
    settings = get_completions_settings()
    settings.update(
        {
            # specific naming for context length
            "num_ctx": context_window,
        }
    )

    # https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-completion
    request = {
        "model":model_name,
        "prompt":prompt,
        "stream": False,
        "options": settings,
        "raw": True,
    }

    if not endpoint.startswith(("http://", "https://")):
        raise ValueError(f"Provided OPENAI_API_BASE value ({endpoint}) must begin with http:// or https://")
    
    try:
        uri = urljoin(endpoint.strip("/") + "/" ,OLLAMA_API_BASE_URL.strip("/"))
        response = requests.post(uri, json=request)
        if response.status_code == 200:
            result_full = response.json()
            printd(f"JSON API response:\n{result_full}")
            result = result_full["response"]

        else:
            Exception(
                f"API call got non-200 response code (code={response.status_code}, msg={response.text}) for address: {uri}."
                + f" Make sure that the ollama API server is running and reachable at {uri}."
            )
        # https://github.com/jmorganca/ollama/blob/main/docs/api.md#response
        # eval_count: number of tokens in the response
        completion_tokens = result_full.get("eval_count", None)
        total_tokens = prompt_tokens + completion_tokens if completion_tokens is not None else None

        usage = {
            "prompt_tokens": prompt_tokens, 
            "completion_tokens":completion_tokens,
            "total_tokens":total_tokens
        }

        return result,usage

    except:
        raise 


if __name__ == "__main__":
    context_window = 8192
    endpoint = "http://localhost:11434"
    model_name = "llama3:latest"

    reuslt, usage = get_ollama_completion(endpoint=endpoint,model_name=model_name,prompt="write hello world in python",context_window=context_window)

    console.print(reuslt)
    console.print(usage)