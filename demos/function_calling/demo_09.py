import requests
import json
import sys
import yfinance as yf

company_name = "Google"

schema = {
    "company": {
        "type": "string",
        "description": "Name of the company"
    },
    "ticker": {
        "type": "string",
        "description": "Ticker symbol of the company"
    }
}

payload = {
    "model": "llama2",
    "messages": [
        {
            "role": "system",
            "content": f"You are a helpful AI assistant. The user will enter a company name and the assistant will return the ticker symbol and current stock price of the company. Output in JSON using the schema defined here: {json.dumps(schema)}."
        },
        {"role": "user", "content": "Apple"},
        {"role": "assistant", "content": json.dumps({"company": "Apple", "ticker": "AAPL"})},  # Example static data
        {"role": "user", "content": company_name}
    ],
    "format": "json",
    "stream": False
}

response = requests.post("http://localhost:11434/api/chat", json=payload)
company_info = json.loads(response.json()["message"]["content"])

# Fetch the current stock price using yfinance
ticker_symbol = company_info['ticker']

print(f"{ticker_symbol=}")
stock = yf.Ticker(ticker_symbol)
print(f"{stock=}")
hist = stock.history(period="1d")
print(type(hist))
print(hist.head())
exit(0)


stock_price = hist['Close'].iloc[-1]

print(f"The current stock price of {company_info['company']} ({ticker_symbol}) is USD {stock_price}.")