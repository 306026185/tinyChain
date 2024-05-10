from langchain_core.prompts import PromptTemplate

prompt_template = PromptTemplate.from_template(
    "Tell me a {adjective} joke about {content}."
)

print(type(prompt_template))
print(dir(prompt_template))
print(prompt_template)

prompt_template.format(adjective="funny", content="chickens")