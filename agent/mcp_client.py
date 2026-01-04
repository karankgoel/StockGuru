import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import os

class MCPToolAdapter:
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session = None
        self.exit_stack = AsyncExitStack()
        self._tools = {}

    async def start(self):
        """Starts the MCP server and client session."""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script_path],
            env=os.environ.copy()
        )
        
        transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.session = await self.exit_stack.enter_async_context(ClientSession(transport[0], transport[1]))
        await self.session.initialize()
        
        # Discover tools
        result = await self.session.list_tools()
        for tool in result.tools:
            self._tools[tool.name] = tool

    async def call_tool(self, name: str, arguments: dict):
        if not self.session:
            raise RuntimeError("MCP Client not started")
        result = await self.session.call_tool(name, arguments)
        return result.content[0].text

    async def close(self):
        await self.exit_stack.aclose()

    def get_tool_function(self, tool_name: str):
        """Returns a synchronous callable wrapper for the tool."""
        # Note: synchronicity is tricky here if the agent runner is synchronous.
        # But ADK's InMemoryRunner is async-friendly or we may need to run run_until_complete.
        # For simplicity, if ADK expects sync functions, we might need a global event loop or run_coroutine_threadsafe.
        # However, looking at orchestrator.py, the specialists use `agent.run(prompt)` which is sync.
        
        # We'll create a sync wrapper that runs the async call.
        
        def wrapper(**kwargs):
            try:
                # Check for running loop
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                 # This is tricky if we are already in a loop.
                 # But ADK's agent.run() usually blocks.
                 raise RuntimeError("Cannot call async tool from sync context with running loop")
            
            return loop.run_until_complete(self.call_tool(tool_name, kwargs))
            
        return wrapper
