import os
from google.adk import Agent

class PortfolioAnalyst:
    def __init__(self, model="gemini-pro", tools=None):
        self.model = model
        self.tools = tools or []
        self.instruction = """You are a Portfolio Analyst & Fund Manager.
            Your goal is to provide advice on asset allocation, ETFs, mutual funds, and investor portfolios.
            
            STRICT RULES:
            1. Use 'search_web' to find popular funds, ETFs, or portfolios of famous investors (e.g., "Ray Dalio portfolio").
            2. Use 'get_etf_info' to get details on specific ETFs found in search or requested by user.
            3. Use 'get_stock_history' to check performance if needed.
            4. Focus on diversification, expense ratios, and risk management.
            5. When recommending funds, explain WHY they fit the user's goal (e.g., "VTI for broad exposure").
            6. If you cannot find info, state "Data Unavailable"."""

    def _create_agent(self):
        from google.adk.models import Gemini
        return Agent(
            name="portfolio_analyst",
            model=Gemini(model=self.model),
            tools=self.tools,
            instruction=self.instruction
        )

    def analyze(self, query: str) -> str:
        prompt = f"Analyze and provide recommendations for: {query}"
        from agent.utils import run_agent_sync
        return run_agent_sync(self._create_agent, prompt)
