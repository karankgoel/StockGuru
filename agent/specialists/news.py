import os
from google.adk import Agent
from google.adk import Agent
# Tools will be injected

class NewsAnalyst:
    def __init__(self, model="gemini-pro", tools=None):
        self.model = model
        self.tools = tools or []
        self.instruction = """You are a News Analyst.
            Your goal is to research recent news and gauge market sentiment.
            
            STRICT RULES:
            1. Use the provided tools to fetch the latest news.
            2. Summarize key headlines and cite the source/link if available.
            3. Determine if the sentiment is positive, negative, or neutral based ONLY on the fetched news.
            4. If no recent news is found, state "No recent news found". DO NOT HALLUCINATE news.
            5. Focus on potential impact on the stock price."""

    def _create_agent(self):
        from google.adk.models import Gemini
        return Agent(
            name="news_analyst",
            model=Gemini(model=self.model),
            tools=self.tools,
            instruction=self.instruction
        )

    def analyze(self, symbol: str) -> str:
        prompt = f"Get the latest news for {symbol} and summarize the sentiment."
        from agent.utils import run_agent_sync
        return run_agent_sync(self._create_agent, prompt)
