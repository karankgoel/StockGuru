import os
from google.adk import Agent
from google.adk import Agent
# Tools will be injected


class TechnicalAnalyst:
    def __init__(self, model="gemini-pro", tools=None):
        self.agent = Agent(
            name="technical_analyst",
            model=model,
            tools=tools or [],
            instruction="""You are a Technical Analyst. 
            Your goal is to analyze stock charts, patterns, and technical indicators.
            
            STRICT RULES:
            1. Use the provided tools to get historical data and technical summaries (RSI, MACD, etc.).
            2. CITE SPECIFIC VALUES. Do not say "RSI is high", say "RSI is 75.4".
            3. Identify Support and Resistance levels based on the provided history.
            4. Provide a clear bullish, bearish, or neutral signal based ONLY on technical data.
            5. If data is missing, state "Data Unavailable". DO NOT GUESS.
            6. Do not consider news or fundamentals."""
        )

    def analyze(self, symbol: str) -> str:
        prompt = f"Analyze the technical indicators and price history for {symbol}. Provide a technical assessment."
        try:
            response = self.agent.run(prompt)
            return response.text
        except Exception as e:
            return f"Technical Analysis failed: {e}"
