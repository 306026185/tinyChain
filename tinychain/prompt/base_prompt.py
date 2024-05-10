
import re
from abc import ABC
from typing import Optional,List,Dict,Any,Union,Tuple

from tinychain.message.messages import BaseMessage
from tinychain.utils import get_variables

LikeMessageRepresentation = Union[str,Union[List[Union[Tuple[str,Any],BaseMessage]]]]

class StringPromptTemplate():
    def __init__(self,template:str,
                 input_variables:Optional[list[str]],
                 ) -> None:
        self.template = template
        self.input_variables = input_variables

    def format(self,**kwargs):
        return self.template.format(**kwargs)

class BasePromptTemplate(StringPromptTemplate,ABC):

    def __init__(self,
            template:LikeMessageRepresentation,
            input_variables: List[str],
            input_types: Optional[Dict[str, Any]]=None,
            name:Optional[str]=None) -> None:
        self.template = template
        self.input_variables = input_variables
        self.input_types = input_types
        self.name = name

    def format_messages(self, **kwargs: Any) -> List[BaseMessage]:
        """Format kwargs into a list of messages."""


class PromptTemplate(BasePromptTemplate):

    def __init__(self, 
                 template: LikeMessageRepresentation, 
                 input_variables: List[str], 
                 input_types: Union[Dict[str, Any],None] = None, 
                 name: Union[str , None] = None) -> None:
        super().__init__(template, input_variables, input_types, name)


    @classmethod
    def from_template(cls,template):
        input_variables = get_variables(template)
 
        return cls(template=template,input_variables=input_variables)


    def invoke(self,input:dict):
        pass
