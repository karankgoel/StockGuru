import os
from google.adk import Agent
from google.adk import Agent
# Tools will be injected

class FundamentalAnalyst:
    def __init__(self, model="gemini-pro", tools=None):
        self.agent = Agent(
            name="fundamental_analyst",
            model=model,
            tools=tools or [],
            instruction="""You are a Fundamental Analyst.
            Your goal is to evaluate the company's business model, sector, and long-term prospects.
            
            STRICT RULES:
            1. Use the provided tools to get the company profile.
            2. Base your assessment ONLY on the provided profile data (Sector, Industry, Summary).
            3. Do not make up financial figures (revenue, PE ratio) if they are not in the data.
            4. Provide an assessment of the company's fundamental strength."""
        )

    def analyze(self, symbol: str) -> str:
        prompt = f"Analyze the company profile for {symbol}. What is the business model and sector outlook?"
        try:
            response = self.agent.run(prompt)
            return response.text
        except Exception as e:
            return f"Fundamental Analysis failed: {e}"
