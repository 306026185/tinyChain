from dataclasses import dataclass
from tinychain.utils import get_variables
from tinychain.message.messages import ChatMessage

@dataclass
class MessagesPlaceholder:
    variable_name:str

    
class ChatMessagePromptTemplate:

    def format(subject="force"):
        return 

    @classmethod
    def from_template(cls,template):
        input_variables = get_variables(template)
 
        return cls(role=role,template=template,input_variables=input_variables)
