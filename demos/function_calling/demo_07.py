from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
import yfinance as yf

from rich.console import Console

import instructor

console = Console()

company = "Google"

class StockInfo(BaseModel):
    company: str = Field(..., description="Name of the company")
    ticker: str = Field(..., description="Ticker symbol of the company")

# enables `response_model` in create call
client = instructor.patch(
    OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    ),
    mode=instructor.Mode.JSON,
)

resp = client.chat.completions.create(
    model="llama3",
    messages=[
        {
            "role": "user",
            "content": f"Return the company name and the ticker symbol of the {company}."
        }
    ],
    response_model=StockInfo,
    max_retries=10
)
console.print(resp.model_dump_json(indent=2))

stock = yf.Ticker(resp.ticker)
hist = stock.history(period="1d")
print(type(hist))
exit(0)
stock_price = hist['Close'].iloc[-1]
console.print(f"The stock price of the {resp.company} is {stock_price}. USD")