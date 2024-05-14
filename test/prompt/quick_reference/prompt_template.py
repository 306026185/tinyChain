from rich.console import Console

from tinychain.prompt.base_prompt import PromptTemplate

console = Console()

prompt_template = PromptTemplate.from_template(
    "Tell me a {adjective} joke about {content}."
)
prompt_one = prompt_template.format(adjective="funny", content="chickens")

console.print(prompt_one)

prompt_template = PromptTemplate.from_template("Tell me a joke")
prompt_two = prompt_template.format()

console.print(prompt_two)

