from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
import os
from google.adk import Agent

from agent.models.factory import get_model


# Initialize Model from Factory
# model = get_model()  <-- MOVED INSIDE CLASS

class AdvisorAgent:
    def __init__(self, model_instance=None):
        if "GOOGLE_API_KEY" not in os.environ:
             # Just a warning
            print("Warning: GOOGLE_API_KEY not found in environment variables.")

        # Initialize MCP Client
        from agent.mcp_client import MCPToolAdapter
        import asyncio
        import threading
        
        # Path to the MCP server
        server_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "servers", "stock_data", "mcp_server.py")
        self.mcp_adapter = MCPToolAdapter(server_path)
        
        # Start MCP Client on a dedicated background thread/loop
        # This ensures the loop stays alive for the duration of the agent
        def start_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self._mcp_loop = asyncio.new_event_loop()
        self._mcp_thread = threading.Thread(target=start_loop, args=(self._mcp_loop,), daemon=True)
        self._mcp_thread.start()
        
        # Start the adapter on the background loop
        future = asyncio.run_coroutine_threadsafe(self.mcp_adapter.start(), self._mcp_loop)
        try:
            future.result(timeout=10) # Wait for startup
        except Exception as e:
            print(f"Failed to start MCP Client: {e}")
            # Fallback or error out? For now, we proceed but tools might be empty/broken.

    def run(self, user_input):
        try:
            # Create a fresh model instance for this run
            # This ensures it binds to the correct event loop if needed
            model_instance = get_model()
            # Use the same model for specialists to ensure consistency
            model_name = os.environ.get("LLM_MODEL", "gemini-2.0-flash")

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
                self.mcp_adapter.get_tool_function("get_stock_profile"),
                self.mcp_adapter.get_tool_function("get_detailed_stock_info")
            ]
            
            # Portfolio Tools
            portfolio_tools = [
                self.mcp_adapter.get_tool_function("search_web"),
                self.mcp_adapter.get_tool_function("get_etf_info"),
                self.mcp_adapter.get_tool_function("get_stock_history")
            ]
            
            # Get all tools directly for the main agent
            all_tools = tech_tools + news_tools + fund_tools + portfolio_tools

            agent = Agent(
                name="advisor_agent",
                model=model_instance,
                tools=all_tools,
                instruction="""You are a Senior Investment Advisor.
                Your goal is to provide comprehensive Buy, Sell, or Hold recommendations, OR Portfolio Advice.
                
                You have access to the following tools:
                - get_stock_history: Get historical price data for a stock
                - get_technical_summary: Get technical indicators (RSI, MACD, etc.) for a stock
                - get_stock_news: Get recent news articles for a stock
                - get_stock_profile: Get company profile and fundamental data
                - search_web: Search the web for information
                - get_etf_info: Get information about ETFs
                
                STRICT PROCESS:
                
                IF User asks for Stock Analysis (e.g. "Analyze AAPL"):
                    1. Use get_technical_summary to check technical indicators
                    2. Use get_stock_news to check recent news and sentiment
                    3. Use get_stock_profile to check the company fundamentals
                    4. Synthesize all the data
                    5. Provide a clear recommendation (Buy/Sell/Hold) with reasoning, price prediction, and risks
                    
                IF User asks for Portfolio/Fund Advice (e.g. "Best tech ETFs" or "Warren Buffett portfolio"):
                    1. Use search_web to find relevant information
                    2. Use get_etf_info for specific ETF details if needed
                    3. Use get_stock_history to check performance if needed
                    4. Provide clear, actionable advice
                
                IMPORTANT:
                - If a tool returns an error or "Data Unavailable", state that clearly
                - DO NOT make up facts or numbers
                - Be decisive but balanced
                - Always pass the stock symbol to tools that require it"""
            )

            # Initialize Runner
            enhanced_runner = InMemoryRunner(agent=agent, app_name="agents")
            
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
                
                # Check for ModelResponseEvent which contains the text
                # Try event.response first (standard ModelResponseEvent)
                if hasattr(event, 'response') and event.response:
                    try:
                        text = event.response.text
                        if text:
                            response_text = text
                    except Exception:
                        pass
                
                # Fallback: Content attribute directly (some event types)
                elif hasattr(event, 'content') and event.content:
                     try:
                        # content is likely a Content object with parts
                        if hasattr(event.content, 'parts'):
                            parts = event.content.parts
                            text_parts = [p.text for p in parts if hasattr(p, 'text') and p.text]
                            if text_parts:
                                response_text = "\n".join(text_parts)
                     except Exception:
                        pass
                    
            return response_text
        except Exception as e:
            return f"Advisor failed: {e}"
