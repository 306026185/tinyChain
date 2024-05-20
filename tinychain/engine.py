import os
import sys
import json
import traceback

import typer
from rich.console import Console

from tinychain.config import TinyChainConfig
import tinychain.agent as agent
import questionary

import tinychain.system as system
from tinychain.streaming_interface import AgentRefreshStreamingInterface

def clear_line(console, strip_ui=False):
    if strip_ui:
        return
    if os.name == "nt":  # for windows
        console.print("\033[A\033[K", end="")
    else:  # for linux
        sys.stdout.write("\033[2K\033[G")
        sys.stdout.flush()


def run_agent_loop(
        tinychain_agent: agent.Agent, 
        config: TinyChainConfig, 
        first,  
        no_verify=False, 
        cfg=None, 
        strip_ui=False, 
        stream=False
):
    if isinstance(tinychain_agent.interface, AgentRefreshStreamingInterface):
        # tinychain_agent.interface.toggle_streaming(on=stream)
        if not stream:
            tinychain_agent.interface = tinychain_agent.interface.nonstreaming_interface
    
    console = Console()

    counter = 0
    user_input = None
    skip_next_user_input = False
    user_message = None
    # 
    USER_GOES_FIRST = first

    if not USER_GOES_FIRST:
        console.input("[bold cyan]Hit enter to begin (will request first TinyChain message)[/bold cyan]\n")
        clear_line(console, strip_ui=strip_ui)
        print()

    multiline_input = False

    

    while True:
        if not skip_next_user_input and (counter > 0 or USER_GOES_FIRST):
            # Ask for user input
            if not stream:
                print()
            user_input = questionary.text(
                "Enter your message:",
                multiline=multiline_input,
                qmark=">",
            ).ask()
            clear_line(console, strip_ui=strip_ui)
            if not stream:
                print()

            # Gracefully exit on Ctrl-C/D
            if user_input is None:
                user_input = "/exit"

            user_input = user_input.rstrip()

            if user_input.startswith("!"):
                print(f"Commands for CLI begin with '/' not '!'")
                continue

            if user_input == "":
                # no empty messages allowed
                print("Empty input received. Try again!")
                continue

            # Handle CLI commands
            # Commands to not get passed as input to TinyChain
            if user_input.startswith("/"):
                # updated agent save functions
                if user_input.lower() == "/exit":
                    # tinychain_agent.save()
                    # agent.save_agent(tinychain_agent, ms)
                    break
                elif user_input.lower() == "/save" or user_input.lower() == "/savechat":
                    # tinychain_agent.save()
                    # agent.save_agent(tinychain_agent, ms)
                    continue
                elif user_input.lower() == "/attach":
                    # TODO: check if agent already has it

                    # TODO: check to ensure source embedding dimentions/model match agents, and disallow attachment if not
                    # TODO: alternatively, only list sources with compatible embeddings, and print warning about non-compatible sources

                    data_source_options = ms.list_sources(user_id=tinychain_agent.agent_state.user_id)
                    if len(data_source_options) == 0:
                        typer.secho(
                            'No sources available. You must load a souce with "tinychain load ..." before running /attach.',
                            fg=typer.colors.RED,
                            bold=True,
                        )
                        continue

                    # determine what sources are valid to be attached to this agent
                    valid_options = []
                    invalid_options = []
                    for source in data_source_options:
                        if (
                            source.embedding_model == tinychain_agent.agent_state.embedding_config.embedding_model
                            and source.embedding_dim == tinychain_agent.agent_state.embedding_config.embedding_dim
                        ):
                            valid_options.append(source.name)
                        else:
                            # print warning about invalid sources
                            typer.secho(
                                f"Source {source.name} exists but has embedding dimentions {source.embedding_dim} from model {source.embedding_model}, while the agent uses embedding dimentions {tinychain_agent.agent_state.embedding_config.embedding_dim} and model {tinychain_agent.agent_state.embedding_config.embedding_model}",
                                fg=typer.colors.YELLOW,
                            )
                            invalid_options.append(source.name)

                    # prompt user for data source selection
                    data_source = questionary.select("Select data source", choices=valid_options).ask()

                    # attach new data
                    # attach(tinychain_agent.agent_state.name, data_source)
                    source_connector = StorageConnector.get_storage_connector(
                        TableType.PASSAGES, config, user_id=tinychain_agent.agent_state.user_id
                    )
                    tinychain_agent.attach_source(data_source, source_connector, ms)

                    continue

                elif user_input.lower() == "/dump" or user_input.lower().startswith("/dump "):
                    # Check if there's an additional argument that's an integer
                    command = user_input.strip().split()
                    amount = int(command[1]) if len(command) > 1 and command[1].isdigit() else 0
                    if amount == 0:
                        tinychain_agent.interface.print_messages(tinychain_agent._messages, dump=True)
                    else:
                        tinychain_agent.interface.print_messages(tinychain_agent._messages[-min(amount, len(tinychain_agent.messages)) :], dump=True)
                    continue

                elif user_input.lower() == "/dumpraw":
                    tinychain_agent.interface.print_messages_raw(tinychain_agent._messages)
                    continue

                elif user_input.lower() == "/memory":
                    print(f"\nDumping memory contents:\n")
                    print(f"{str(tinychain_agent.memory)}")
                    print(f"{str(tinychain_agent.persistence_manager.archival_memory)}")
                    print(f"{str(tinychain_agent.persistence_manager.recall_memory)}")
                    continue

                elif user_input.lower() == "/model":
                    if tinychain_agent.model == "gpt-4":
                        tinychain_agent.model = "gpt-3.5-turbo-16k"
                    elif tinychain_agent.model == "gpt-3.5-turbo-16k":
                        tinychain_agent.model = "gpt-4"
                    print(f"Updated model to:\n{str(tinychain_agent.model)}")
                    continue

                elif user_input.lower() == "/pop" or user_input.lower().startswith("/pop "):
                    # Check if there's an additional argument that's an integer
                    command = user_input.strip().split()
                    pop_amount = int(command[1]) if len(command) > 1 and command[1].isdigit() else 3
                    n_messages = len(tinychain_agent.messages)
                    MIN_MESSAGES = 2
                    if n_messages <= MIN_MESSAGES:
                        print(f"Agent only has {n_messages} messages in stack, none left to pop")
                    elif n_messages - pop_amount < MIN_MESSAGES:
                        print(f"Agent only has {n_messages} messages in stack, cannot pop more than {n_messages - MIN_MESSAGES}")
                    else:
                        print(f"Popping last {pop_amount} messages from stack")
                        for _ in range(min(pop_amount, len(tinychain_agent.messages))):
                            tinychain_agent.messages.pop()
                    continue

                elif user_input.lower() == "/retry":
                    # TODO this needs to also modify the persistence manager
                    print(f"Retrying for another answer")
                    while len(tinychain_agent.messages) > 0:
                        if tinychain_agent.messages[-1].get("role") == "user":
                            # we want to pop up to the last user message and send it again
                            user_message = tinychain_agent.messages[-1].get("content")
                            tinychain_agent.messages.pop()
                            break
                        tinychain_agent.messages.pop()

                elif user_input.lower() == "/rethink" or user_input.lower().startswith("/rethink "):
                    # TODO this needs to also modify the persistence manager
                    if len(user_input) < len("/rethink "):
                        print("Missing text after the command")
                        continue
                    for x in range(len(tinychain_agent.messages) - 1, 0, -1):
                        if tinychain_agent.messages[x].get("role") == "assistant":
                            text = user_input[len("/rethink ") :].strip()
                            tinychain_agent.messages[x].update({"content": text})
                            break
                    continue

                elif user_input.lower() == "/rewrite" or user_input.lower().startswith("/rewrite "):
                    # TODO this needs to also modify the persistence manager
                    if len(user_input) < len("/rewrite "):
                        print("Missing text after the command")
                        continue
                    for x in range(len(tinychain_agent.messages) - 1, 0, -1):
                        if tinychain_agent.messages[x].get("role") == "assistant":
                            text = user_input[len("/rewrite ") :].strip()
                            # Get the current message content
                            # The rewrite target is the output of send_message
                            message_obj = tinychain_agent._messages[x]
                            if message_obj.tool_calls is not None and len(message_obj.tool_calls) > 0:
                                # Check that we hit an assistant send_message call
                                name_string = message_obj.tool_calls[0].function.get("name")
                                if name_string is None or name_string != "send_message":
                                    print("Assistant missing send_message function call")
                                    break  # cancel op
                                args_string = message_obj.tool_calls[0].function.get("arguments")
                                if args_string is None:
                                    print("Assistant missing send_message function arguments")
                                    break  # cancel op
                                args_json = json.loads(args_string, strict=JSON_LOADS_STRICT)
                                if "message" not in args_json:
                                    print("Assistant missing send_message message argument")
                                    break  # cancel op

                                # Once we found our target, rewrite it
                                args_json["message"] = text
                                new_args_string = json.dumps(args_json, ensure_ascii=JSON_ENSURE_ASCII)
                                message_obj.tool_calls[0].function["arguments"] = new_args_string

                                # To persist to the database, all we need to do is "re-insert" into recall memory
                                tinychain_agent.persistence_manager.recall_memory.storage.update(record=message_obj)
                                break
                    continue

                elif user_input.lower() == "/summarize":
                    try:
                        tinychain_agent.summarize_messages_inplace()
                        typer.secho(
                            f"/summarize succeeded",
                            fg=typer.colors.GREEN,
                            bold=True,
                        )
                    except (errors.LLMError, requests.exceptions.HTTPError) as e:
                        typer.secho(
                            f"/summarize failed:\n{e}",
                            fg=typer.colors.RED,
                            bold=True,
                        )
                    continue

                elif user_input.lower().startswith("/add_function"):
                    try:
                        if len(user_input) < len("/add_function "):
                            print("Missing function name after the command")
                            continue
                        function_name = user_input[len("/add_function ") :].strip()
                        result = tinychain_agent.add_function(function_name)
                        typer.secho(
                            f"/add_function succeeded: {result}",
                            fg=typer.colors.GREEN,
                            bold=True,
                        )
                    except ValueError as e:
                        typer.secho(
                            f"/add_function failed:\n{e}",
                            fg=typer.colors.RED,
                            bold=True,
                        )
                        continue
                elif user_input.lower().startswith("/remove_function"):
                    try:
                        if len(user_input) < len("/remove_function "):
                            print("Missing function name after the command")
                            continue
                        function_name = user_input[len("/remove_function ") :].strip()
                        result = tinychain_agent.remove_function(function_name)
                        typer.secho(
                            f"/remove_function succeeded: {result}",
                            fg=typer.colors.GREEN,
                            bold=True,
                        )
                    except ValueError as e:
                        typer.secho(
                            f"/remove_function failed:\n{e}",
                            fg=typer.colors.RED,
                            bold=True,
                        )
                        continue

                # No skip options
                elif user_input.lower() == "/wipe":
                    tinychain_agent = agent.Agent(tinychain_agent.interface)
                    user_message = None

                elif user_input.lower() == "/heartbeat":
                    user_message = system.get_heartbeat()

                elif user_input.lower() == "/memorywarning":
                    user_message = system.get_token_limit_warning()

                elif user_input.lower() == "//":
                    multiline_input = not multiline_input
                    continue

                elif user_input.lower() == "/" or user_input.lower() == "/help":
                    questionary.print("CLI commands", "bold")
                    for cmd, desc in USER_COMMANDS:
                        questionary.print(cmd, "bold")
                        questionary.print(f" {desc}")
                    continue

                else:
                    print(f"Unrecognized command: {user_input}")
                    continue

            else:
                # If message did not begin with command prefix, pass inputs to TinyChain
                # Handle user message and append to messages
                user_message = system.package_user_message(user_input)

        skip_next_user_input = False

        def process_agent_step(user_message, no_verify):
            new_messages, heartbeat_request, function_failed, token_warning, tokens_accumulated = tinychain_agent.step(
                user_message,
                first_message=False,
                skip_verify=no_verify,
                stream=stream,
            )

            skip_next_user_input = False
            if token_warning:
                user_message = system.get_token_limit_warning()
                skip_next_user_input = True
            elif function_failed:
                user_message = system.get_heartbeat(FUNC_FAILED_HEARTBEAT_MESSAGE)
                skip_next_user_input = True
            elif heartbeat_request:
                user_message = system.get_heartbeat(REQ_HEARTBEAT_MESSAGE)
                skip_next_user_input = True

            return new_messages, user_message, skip_next_user_input

        while True:
            try:
                if strip_ui:
                    new_messages, user_message, skip_next_user_input = process_agent_step(user_message, no_verify)
                    break
                else:
                    if stream:
                        # Don't display the "Thinking..." if streaming
                        new_messages, user_message, skip_next_user_input = process_agent_step(user_message, no_verify)
                    else:
                        with console.status("[bold cyan]Thinking...") as status:
                            new_messages, user_message, skip_next_user_input = process_agent_step(user_message, no_verify)
                    break
            except KeyboardInterrupt:
                print("User interrupt occurred.")
                retry = questionary.confirm("Retry agent.step()?").ask()
                if not retry:
                    break
            except Exception as e:
                print("An exception occurred when running agent.step(): ")
                traceback.print_exc()
                retry = questionary.confirm("Retry agent.step()?").ask()
                if not retry:
                    break

        counter += 1

    print("Finished.")


USER_COMMANDS = [
    ("//", "toggle multiline input mode"),
    ("/exit", "exit the CLI"),
    ("/save", "save a checkpoint of the current agent/conversation state"),
    ("/load", "load a saved checkpoint"),
    ("/dump <count>", "view the last <count> messages (all if <count> is omitted)"),
    ("/memory", "print the current contents of agent memory"),
    ("/pop <count>", "undo <count> messages in the conversation (default is 3)"),
    ("/retry", "pops the last answer and tries to get another one"),
    ("/rethink <text>", "changes the inner thoughts of the last agent message"),
    ("/rewrite <text>", "changes the reply of the last agent message"),
    ("/heartbeat", "send a heartbeat system message to the agent"),
    ("/memorywarning", "send a memory warning system message to the agent"),
    ("/attach", "attach data source to agent"),
]
