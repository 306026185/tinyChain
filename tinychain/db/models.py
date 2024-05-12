
from typing import List,Any
from pydantic import BaseModel,Field


class Rec(BaseModel):
    rec_id:str
    create_at:str
    namespace:str
    document:str
    embedding:str
    is_used:bool


class Result(BaseModel):
    documents:List[str]
    ids:List[str]
    distances:List[float]