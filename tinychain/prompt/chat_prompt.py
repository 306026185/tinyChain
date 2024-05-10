
from typing import Dict, List,Any,Union,Tuple

from tinychain.message.messages import BaseMessage,SystemMessage,HumanMessage,AIMessage
from tinychain.prompt.base_prompt import BasePromptTemplate,LikeMessageRepresentation
from tinychain.utils import check_messages_type,get_variables

class BaseChatPromptTemplate(BasePromptTemplate):

    def __init__(self, 
                 template: LikeMessageRepresentation, 
                 input_variables: List[str], 
                 input_types: Union[Dict[str, Any] , None] = None, 
                 name: Union[str, None] = None) -> None:
        super().__init__(template, input_variables, input_types, name)
    
class ChatPromptTemplate(BaseChatPromptTemplate):

    def __getitem__(self,index):
        pass

    def __len__(self)->int:
        pass

    @classmethod
    def from_messages(cls,messages:Union[List[ Union[BaseMessage,Tuple[str,Any]]]]):
        
        messages_list = []
        input_variables = []
        if check_messages_type(messages) == "List[Tuple[str, str]]":

            for message in messages:
                if message[0] in ["system"]:

                    input_variables += get_variables(message[1])
                    messages_list.append(SystemMessage(message[1]))
                elif message[0] in ["user","human"]:
                    input_variables += get_variables(message[1])
                    messages_list.append(HumanMessage(message[1]))
                elif message[0] in  ["ai","assistant"]:
                    input_variables += get_variables(message[1])
                    messages_list.append(AIMessage(message[1]))
                else:
                    raise ValueError("role value shoubld ")
                
            
        elif check_messages_type(messages) == "List[BaseMessage]":
            messages_list = messages
        else:
            raise(ValueError("messages shouble Union[List[ Union[BaseMessage,Tuple[str,Any]]]]"))
        
        return cls(messages_list,input_variables=input_variables)
    
    def from_role_strings(self):
        pass

    def from_strings(self,string_messages):
        pass


    def format_messages(self,**kwargs:Any)->List[BaseMessage]:
        for msg in self.template:
            msg = msg.content.format(**kwargs)
            

        return self.template 
