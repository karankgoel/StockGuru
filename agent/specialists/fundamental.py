import os
from google.adk import Agent
from google.adk import Agent
# Tools will be injected

class FundamentalAnalyst:
    def __init__(self, model="gemini-pro", tools=None):
        self.model = model
        self.tools = tools or []
        self.instruction = """You are a Fundamental Analyst.
            Your goal is to evaluate the company's business model, sector, and long-term prospects.
            
            STRICT RULES:
            1. Use the provided tools to get the company profile.
            2. Base your assessment ONLY on the provided profile data (Sector, Industry, Summary).
            3. Do not make up financial figures (revenue, PE ratio) if they are not in the data.
            4. Provide an assessment of the company's fundamental strength."""

    def _create_agent(self):
        from google.adk.models import Gemini
        return Agent(
            name="fundamental_analyst",
            model=Gemini(model=self.model),
            tools=self.tools,
            instruction=self.instruction
        )

    def analyze(self, symbol: str) -> str:
        prompt = f"Analyze the company profile for {symbol}. What is the business model and sector outlook?"
        from agent.utils import run_agent_sync
        return run_agent_sync(self._create_agent, prompt)
