import os
from google.adk import Agent
from google.adk import Agent
# Tools will be injected

class NewsAnalyst:
    def __init__(self, model="gemini-pro", tools=None):
        self.agent = Agent(
            name="news_analyst",
            model=model,
            tools=tools or [],
            instruction="""You are a News Analyst.
            Your goal is to research recent news and gauge market sentiment.
            
            STRICT RULES:
            1. Use the provided tools to fetch the latest news.
            2. Summarize key headlines and cite the source/link if available.
            3. Determine if the sentiment is positive, negative, or neutral based ONLY on the fetched news.
            4. If no recent news is found, state "No recent news found". DO NOT HALLUCINATE news.
            5. Focus on potential impact on the stock price."""
        )

    def analyze(self, symbol: str) -> str:
        prompt = f"Get the latest news for {symbol} and summarize the sentiment."
        try:
            response = self.agent.run(prompt)
            return response.text
        except Exception as e:
            return f"News Analysis failed: {e}"
