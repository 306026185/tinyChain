import os
import json
from rich.console import Console

from pydantic import BaseModel,EmailStr
from enum import Enum
from typing import Optional

from openai import OpenAI
import instructor

console = Console()
 
client = instructor.patch(
    OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    ),
    mode=instructor.Mode.JSON,
)
class EmailCategory(str,Enum):
    FINANCE= "Finance"
    HR = "HR"
    IT_SUPPORT = "IT Support"
    MANAGEMENT = "Management"
    OTHER = "Other"


class WorkEmail(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: Optional[str] = None
    category:EmailCategory

class EmailClassifier:
    
    def __init__(self,client,model_name) -> None:
        self.client = client
        self.model_name = model_name

    def classify_email(self,email):
        # console.print(f"Classifying the email with subject:{email[:50]}...")
        classification = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "your task is to classify the email into one of the categories:Finance, HR, IT Support, Management, Other. Please return all possible fields"
                },
                {
                    "role":"user",
                    "content":f"email:{email}"
                }
            ],
        )
        return classification.model_dump()

classifier = EmailClassifier(client,"llama3")

