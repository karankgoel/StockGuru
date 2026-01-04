from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
import os
from google.adk import Agent
from agent.specialists.technical import TechnicalAnalyst
from agent.specialists.news import NewsAnalyst
from agent.specialists.fundamental import FundamentalAnalyst
from agent.specialists.portfolio import PortfolioAnalyst
from agent.models.factory import get_model

# Initialize Model from Factory
model = get_model()

class AdvisorAgent:
    def __init__(self, model_instance=model):
        if "GOOGLE_API_KEY" not in os.environ:
             # Just a warning
            print("Warning: GOOGLE_API_KEY not found in environment variables.")

        # Initialize MCP Client
        from agent.mcp_client import MCPToolAdapter
        import asyncio
        
        # Path to the MCP server
        server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "servers", "stock_data", "mcp_server.py")
        self.mcp_adapter = MCPToolAdapter(server_path)
        
        # Start MCP Client and get tools (using a sync wrapper since init is sync)
        # In a production app, we should manage lifecycle better (e.g. async factory).
        # For simplicity here, we'll run the start loop briefly or use the adapter lazily.
        # But we need the tool objects for Agent init.
        
        # We'll use a helper to run async startup synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.mcp_adapter.start())
        except Exception as e:
            print(f"Failed to start MCP Client: {e}")
            # Fallback or error out? For now, we proceed but tools might be empty/broken.
        
        # Get Tool Wrappers
        # Technical Tools
        tech_tools = [
            self.mcp_adapter.get_tool_function("get_stock_history"),
            self.mcp_adapter.get_tool_function("get_technical_summary")
        ]
        
        # News Tools
        news_tools = [
            self.mcp_adapter.get_tool_function("get_stock_news")
        ]
        
        # Fundamental Tools
        fund_tools = [
            self.mcp_adapter.get_tool_function("get_stock_profile")
        ]
        
        # Portfolio Tools
        portfolio_tools = [
            self.mcp_adapter.get_tool_function("search_web"),
            self.mcp_adapter.get_tool_function("get_etf_info"),
            self.mcp_adapter.get_tool_function("get_stock_history")
        ]
        
        # Instantiate specialists with injected tools
        self.tech_agent = TechnicalAnalyst(model=model_instance, tools=tech_tools)
        self.news_agent = NewsAnalyst(model=model_instance, tools=news_tools)
        self.fund_agent = FundamentalAnalyst(model=model_instance, tools=fund_tools)
        self.portfolio_agent = PortfolioAnalyst(model=model_instance, tools=portfolio_tools) # New

        # Definitions for Orchestrator Tools that wrap the specialists
        def consult_technical_analyst(symbol: str) -> str:
            """Gets a tech analysis report."""
            return self.tech_agent.analyze(symbol)

        def consult_news_analyst(symbol: str) -> str:
            """Gets a news analysis report."""
            return self.news_agent.analyze(symbol)

        def consult_fundamental_analyst(symbol: str) -> str:
            """Gets a fundamental analysis report."""
            return self.fund_agent.analyze(symbol)
            
        def consult_portfolio_analyst(query: str) -> str:
            """Gets advice on funds, ETFs, portfolio allocation, or investor portfolios."""
            return self.portfolio_agent.analyze(query)

        self.agent = Agent(
            name="advisor_agent",
            model=model_instance,
            tools=[consult_technical_analyst, consult_news_analyst, consult_fundamental_analyst, consult_portfolio_analyst],
            instruction="""You are a Senior Investment Advisor (Orchestrator).
            Your goal is to provide a comprehensive Buy, Sell, or Hold recommendation, OR Portfolio Advice.
            
            You have a team of analysts:
            1. Technical Analyst: Checks charts, indicators, and support/resistance.
            2. News Analyst: Checks sentiment and headlines.
            3. Fundamental Analyst: Checks business model and sector.
            4. Portfolio Analyst: Specializes in Funds, ETFs, and Asset Allocation.
            
            STRICT PROCESS:
            
            IF User asks for Stock Analysis (e.g. "Analyze AAPL"):
                1. Consult Technical, News, and Fundamental analysts.
                2. Synthesize their reports.
                3. Provide a recommendation (Buy/Sell/Hold) with reasoning, prediction, and risks.
                
            IF User asks for Portfolio/Fund Advice (e.g. "Best tech ETFs" or "Warren Buffett portfolio"):
                1. Consult the Portfolio Analyst.
                2. Provide a clear answer based on their findings.
            
            IMPORTANT:
            - If an analyst returns "Data Unavailable", state that clearly.
            - DO NOT make up facts or numbers.
            - Be decisive but balanced."""
        )


    def run(self, user_input):
        try:
            # Initialize Runner
            enhanced_runner = InMemoryRunner(agent=self.agent, app_name="agents")
            
            # Create session (requires async execution)
            import uuid
            session_id = str(uuid.uuid4())
            async def setup_session():
                return await enhanced_runner.session_service.create_session(
                    user_id="user", 
                    session_id=session_id, 
                    app_name="agents"
                )
            
            import asyncio
            asyncio.run(setup_session())
            
            # Prepare message
            message = Content(parts=[Part(text=user_input)], role="user")
            
            # Run agent
            response_text = ""
            for event in enhanced_runner.run(user_id="user", session_id=session_id, new_message=message):
                # Check for ModelResponseEvent which contains the text
                if hasattr(event, 'response') and event.response and event.response.text:
                    response_text = event.response.text
                    
            return response_text
        except Exception as e:
            return f"Advisor failed: {e}"
