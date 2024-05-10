from __future__ import annotations

import re
from typing import Optional,List,Tuple


from abc import ABC, abstractmethod
from typing import Any,Union

from tinychain.message.messages import BaseMessage,HumanMessage,SystemMessage,AIMessage,ChatMessage



# class PromptRunnable(AbstractRunnable):
#     def __init__(self,prompt) -> None:
#         pass
    
#     def run(self, request: Any) -> str | None:
#         return super().run(request)





    
    

class BaseChatMessagePromptTemplate:

    def __init__(self,role:str,prompt_str:str) -> None:
        self.role = role
        self.prompt_str = prompt_str

    def format(self,**kwargs):

        return ChatMessage(role=self.role,content=self.prompt_str.format(**kwargs))
        


class PromptTemplate(StringPromptTemplate):

    def __init__(self, template: str, input_variables: List[str] | None, input_types: List[dict[str, Any]] | None, name: str | None) -> None:
        super().__init__(template, input_variables, input_types, name)
        self.sequence = []
    @classmethod
    def from_template(cls,template:str):

        matches = re.findall(VARIALBE_EXTRACT_PATTERN, template)

        prompt_variable_dict = {}
        if len(matches) > 0:
            for m in matches:
                prompt_variable_dict[m] = ""

        return StringPromptTemplate(template=template,
                                    input_types=prompt_variable_dict.keys(),
                                    input_variables=['str','str'],
                                    name="prompt")

class BaseChatPromptTemplate(PromptTemplate):

    
    def __init__(self, template: str, input_variables: List[str] | None, input_types: List[dict[str, Any]] | None) -> None:
        name = "chat prompt template"
        super().__init__(template, input_variables, input_types, name)
    
    def format_prompt(self,**kwargs):
        pass

    def format_messages(self,**kwargs):

        for msg in self.messages:
            msg.content = msg.content.format(**kwargs)

        return self.messages 



    

            
                
        

        
        return BaseChatPromptTemplate(messages_list,None,None)


    
        





class ChatMessagePromptTemplate:

    @staticmethod
    def from_template(role:str,template:str):
        return BaseChatMessagePromptTemplate(role=role,prompt_str=template)

class MessagesPlaceholder:
    
    def __init__(self,variable_name:str) -> None:
        self.variable_name = variable_name
    
    


if __name__ == "__main__":

    # test one
    # 创建 prompt 在 prompt 其中，用一对花括号表示一个变量(或者说是占位符)
    prompt_str = "write  a {title} blog about {topic}."
    
    # 通过调用 `PromptTemplate.from_template` 可以创建一个带有一个或者多个变量，当然也可以不带任何变量的模板
    prompt_template_one = PromptTemplate.from_template(prompt_str)
    prompt_one = prompt_template_one.format(title="AI assistant research", topic="AI agent")

    # print(prompt_one)


    # test two
    # 也可以创建一个不带任何变量
    prompt_template_two = PromptTemplate.from_template("Tell me a joke")
    prompt_two = prompt_template_two.format()

    # print(prompt_two)

    # exit(0)

    # zideajang , tinyChain

    # 对于 chatModel 设计 prompt template 也就是多轮对话的模型，由一系列 chatMessage 
    # 也就是针对聊天机器人，然后不断增加 message
    chat_template_one = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful AI bot. Your name is {name}."),
            ("human", "Hello, how are you doing?"),
            ("ai", "I'm doing well, thanks!"),
            ("human", "{user_input}"),
        ]
    )
    chat_messages_one = chat_template_one.format_messages(name="Bob", user_input="What is your name?")
    # print(chat_messages_one)

    chat_template_two = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "You are a helpful assistant that re-writes the user's text to "
                    "sound more upbeat."
                )
            ),
            # 在调用 HumanMessagePromptTemplate 的 from_template 返回的
            # HumanMessagePromptTemplate
            HumanMessagePromptTemplate.from_template("{text}"),
        ]
        
    )
    # 返回的的
    meschat_messages_two = chat_template_two.format_messages(text="I don't like eating tasty things")
    # print(meschat_messages_two)



    prompt = "May the {subject} be with you"

    chat_message_prompt = ChatMessagePromptTemplate.from_template(
        role="Jedi", template=prompt
    )
    chat_message = chat_message_prompt.format(subject="force")
    # print(chat_message)

    # [input:str] <input:>
    human_prompt = "Summarize our conversation so far in {word_count} words."

    # HumanMessage(content=prompt_str)
    human_message_template = HumanMessagePromptTemplate.from_template(human_prompt)

    chat_prompt = ChatPromptTemplate.from_messages(
        [MessagesPlaceholder(variable_name="conversation"), human_message_template]
    )
    print(chat_prompt)


    """
    input_variables=['conversation', 'word_count'] 
    input_types={'conversation': typing.List[typing.Union[
        langchain_core.messages.ai.AIMessage, 
        langchain_core.messages.human.HumanMessage, 
        langchain_core.messages.chat.ChatMessage, 
        langchain_core.messages.system.SystemMessage, 
        langchain_core.messages.function.FunctionMessage, 
        langchain_core.messages.tool.ToolMessage]]} 
    
    messages=[MessagesPlaceholder(variable_name='conversation'), HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['word_count'], template='Summarize our conversation so far in {word_count} words.'))]
    """
    # print(chat_prompt)

    human_message = HumanMessage(content="What is the best way to learn programming?")
    ai_message = AIMessage(
        content="""\
    1. Choose a programming language: Decide on a programming language that you want to learn.

    2. Start with the basics: Familiarize yourself with the basic programming concepts such as variables, data types and control structures.

    3. Practice, practice, practice: The best way to learn programming is through hands-on experience\
    """
    )

    chat_prompt.format_prompt(
        conversation=[human_message, ai_message], word_count="10"
    ).to_messages()

    """
    [HumanMessage(content='What is the best way to learn programming?'),
    AIMessage(content='1. Choose a programming language: Decide on a programming language that you want to learn.\n\n2. Start with the basics: Familiarize yourself with the basic programming concepts such as variables, data types and control structures.\n\n3. Practice, practice, practice: The best way to learn programming is through hands-on experience'),
    HumanMessage(content='Summarize our conversation so far in 10 words.')]
    """

    # prompt_template = PromptTemplate.from_template(
    #     "Tell me a {adjective} joke about {content}."
    # )
    # generate_prompt = prompt_template.format(adjective="funny", content="chickens")
    # # assert generate_prompt
