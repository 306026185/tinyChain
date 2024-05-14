from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown

console = Console()

from tinychain.llm.ollama_chat_model import OllamaChatbotAI

rsp = OllamaChatbotAI().invoke("write read csv file code in python")

md = Markdown(rsp)
console.print(md)

feed_back = Prompt.ask("Enter your feed back ([[bold]y[/]es|[bold]n[/]o])",default="Y")
console.print(feed_back)
if feed_back.lower() == "y":
    console.print(":robot: thank you for usage")
else:
    suggestion  = Prompt.ask("Please Enter your suggestion",default="try again")
    # console.print(suggestion)

    















# if __name__ == "__main__":
#     human_in_loop_chain = HumanInLoopChainContext()

#     human_in_loop_chain.add_prompt("some prompt")
    # human_in_loop_chain.review_response()