import os
from google.adk import Agent

class PortfolioAnalyst:
    def __init__(self, model="gemini-pro", tools=None):
        self.agent = Agent(
            name="portfolio_analyst",
            model=model,
            tools=tools or [],
            instruction="""You are a Portfolio Analyst & Fund Manager.
            Your goal is to provide advice on asset allocation, ETFs, mutual funds, and investor portfolios.
            
            STRICT RULES:
            1. Use 'search_web' to find popular funds, ETFs, or portfolios of famous investors (e.g., "Ray Dalio portfolio").
            2. Use 'get_etf_info' to get details on specific ETFs found in search or requested by user.
            3. Use 'get_stock_history' to check performance if needed.
            4. Focus on diversification, expense ratios, and risk management.
            5. When recommending funds, explain WHY they fit the user's goal (e.g., "VTI for broad exposure").
            6. If you cannot find info, state "Data Unavailable"."""
        )

    def analyze(self, query: str) -> str:
        prompt = f"Analyze and provide recommendations for: {query}"
        try:
            response = self.agent.run(prompt)
            return response.text
        except Exception as e:
            return f"Portfolio Analysis failed: {e}"
