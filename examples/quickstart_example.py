import uuid
import typer

from rich.console import Console

from tinychain.utils import printd
from tinychain.config import TinyChainConfig
from tinychain.data_type import EmbeddingConfig,LLMConfig,Preset
from tinychain.agent.agent import Agent
from tinychain.presets.presets import get_default_presets

console = Console()

# TODO 放置在某一个文件
config = {
    "context_window": 8192,
    "model_endpoint_type": "ollama",
    "model_endpoint": "http://localhost:11434",
    "model": "llama3:latest",
    "embedding_endpoint_type": "ollama",
    "embedding_endpoint": "http://localhost:11434",
    "embedding_model": "nomic-embed-text:latest",
    "embedding_dim": 1024,
    "embedding_chunk_size": 300
}


def set_config_with_dict(new_config: dict) -> (TinyChainConfig, bool):

    old_config = TinyChainConfig.load()
    modified = False
    for k, v in vars(old_config).items():
        if k in new_config:
            if v != new_config[k]:
                printd(f"Replacing config {k}: {v} -> {new_config[k]}")
                modified = True
                # old_config[k] = new_config[k]
                setattr(old_config, k, new_config[k])  # Set the new value using dot notation
            else:
                printd(f"Skipping new config {k}: {v} == {new_config[k]}")

    # update embedding config
    if old_config.default_embedding_config:
        for k, v in vars(old_config.default_embedding_config).items():
            if k in new_config:
                if v != new_config[k]:
                    printd(f"Replacing config {k}: {v} -> {new_config[k]}")
                    modified = True
                    # old_config[k] = new_config[k]
                    setattr(old_config.default_embedding_config, k, new_config[k])
                else:
                    printd(f"Skipping new config {k}: {v} == {new_config[k]}")
    else:
        modified = True
        fields = ["embedding_model", "embedding_dim", "embedding_chunk_size", "embedding_endpoint", "embedding_endpoint_type"]
        args = {}
        for field in fields:
            if field in new_config:
                args[field] = new_config[field]
                printd(f"Setting new config {field}: {new_config[field]}")
        old_config.default_embedding_config = EmbeddingConfig(**args)

    # update llm config
    if old_config.default_llm_config:
        for k, v in vars(old_config.default_llm_config).items():
            if k in new_config:
                if v != new_config[k]:
                    printd(f"Replacing config {k}: {v} -> {new_config[k]}")
                    modified = True
                    # old_config[k] = new_config[k]
                    setattr(old_config.default_llm_config, k, new_config[k])
                else:
                    printd(f"Skipping new config {k}: {v} == {new_config[k]}")
    else:
        modified = True
        fields = ["model", "model_endpoint", "model_endpoint_type", "model_wrapper", "context_window"]
        args = {}
        for field in fields:
            if field in new_config:
                args[field] = new_config[field]
                printd(f"Setting new config {field}: {new_config[field]}")
        old_config.default_llm_config = LLMConfig(**args)
    return (old_config, modified)

def main():
    terminal = True
    printd("JSON config file downloaded successfully.")
    new_config, config_was_modified = set_config_with_dict(config)
    console.print(new_config,config_was_modified)

    if config_was_modified:
        printd(f"Saving new config file.")
        new_config.save()
        typer.secho(f"📖 TinyChain configuration file updated!", fg=typer.colors.GREEN)
        typer.secho(
            "\n".join(
                [
                    f"🧠 model\t-> {new_config.default_llm_config.model}",
                    f"🖥️  endpoint\t-> {new_config.default_llm_config.model_endpoint}",
                ]
            ),
            fg=typer.colors.GREEN,
        )
    else:
        typer.secho(f"📖 TinyChain configuration file unchanged.", fg=typer.colors.WHITE)
        typer.secho(
            "\n".join(
                [
                    f"🧠 model\t-> {new_config.default_llm_config.model}",
                    f"🖥️  endpoint\t-> {new_config.default_llm_config.model_endpoint}",
                ]
            ),
            fg=typer.colors.WHITE,
        )

    # 'terminal' = quickstart was run alone, in which case we should guide the user on the next command
    if terminal:
        if config_was_modified:
            typer.secho('⚡ Run "tinychain run" to create an agent with the new config.', fg=typer.colors.YELLOW)
        else:
            typer.secho('⚡ Run "tinychain run" to create an agent.', fg=typer.colors.YELLOW)
    
    console.print(new_config)  


    preset_obj = get_default_presets(user_id=uuid.uuid4(),)
    exit(0)



    ms.get_preset(name=preset if preset else config.preset, user_id=user.id)
    human_obj = ms.get_human(human, user.id)
    persona_obj = ms.get_persona(persona, user.id)
    if preset_obj is None:
        # create preset records in metadata store
        from memgpt.presets.presets import add_default_presets

        add_default_presets(user.id, ms)
        # try again
        preset_obj = ms.get_preset(name=preset if preset else config.preset, user_id=user.id)
        if preset_obj is None:
            typer.secho("Couldn't find presets in database, please run `memgpt configure`", fg=typer.colors.RED)
            sys.exit(1)
    if human_obj is None:
        typer.secho("Couldn't find human {human} in database, please run `memgpt add human`", fg=typer.colors.RED)
    if persona_obj is None:
        typer.secho("Couldn't find persona {persona} in database, please run `memgpt add persona`", fg=typer.colors.RED)

    # Overwrite fields in the preset if they were specified
    preset_obj.human = ms.get_human(human, user.id).text
    preset_obj.persona = ms.get_persona(persona, user.id).text

    typer.secho(f"->  🤖 Using persona profile: '{preset_obj.persona_name}'", fg=typer.colors.WHITE)
    typer.secho(f"->  🧑 Using human profile: '{preset_obj.human_name}'", fg=typer.colors.WHITE)

    preset_obj = Preset(
        name="preset",
        id=uuid.uuid4(),
        description= ""
    )

    tinchain_agent = Agent(
        interface=interface(),
        name="test_agent",
        created_by=datetime.new,
        preset=preset_obj,
        llm_config=new_config,
        embedding_config=embedding_config,
        # gpt-3.5-turbo tends to omit inner monologue, relax this requirement for now
        first_message_verify_mono=True if (model is not None and "gpt-4" in model) else False,
    )
if __name__ == "__main__":
    main()

