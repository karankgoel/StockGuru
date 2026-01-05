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
        print(f"DEBUG: MCPToolAdapter.start() called on loop {asyncio.get_running_loop()}")
        self._loop = asyncio.get_running_loop() # Capture the loop we are started on
        
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
        print("DEBUG: MCPToolAdapter.start() finished")

    async def call_tool(self, name: str, arguments: dict):
        if not self.session:
            raise RuntimeError("MCP Client not started")
        result = await self.session.call_tool(name, arguments)
        return result.content[0].text

    async def close(self):
        print(f"DEBUG: MCPToolAdapter.close() called. Stack: {len(str(self.exit_stack))}")
        import traceback
        traceback.print_stack()
        await self.exit_stack.aclose()

    def get_tool_function(self, tool_name: str):
        """Returns a synchronous callable wrapper for the tool with proper signature."""
        
        # Get tool schema from MCP server
        tool_schema = None
        if hasattr(self, '_tools') and tool_name in self._tools:
            tool_schema = self._tools[tool_name]
        
        # Build parameter list from schema
        params = []
        param_types = {}
        if tool_schema and hasattr(tool_schema, 'inputSchema') and tool_schema.inputSchema:
            schema = tool_schema.inputSchema
            if isinstance(schema, dict) and 'properties' in schema:
                for param_name, param_info in schema['properties'].items():
                    # Map JSON schema types to Python types
                    param_type = param_info.get('type', 'string')
                    if param_type == 'string':
                        param_types[param_name] = 'str'
                    elif param_type == 'integer':
                        param_types[param_name] = 'int'
                    elif param_type == 'number':
                        param_types[param_name] = 'float'
                    elif param_type == 'boolean':
                        param_types[param_name] = 'bool'
                    else:
                        param_types[param_name] = 'str'
                    
                    params.append(f"{param_name}: {param_types[param_name]}")
        
        # Create function signature
        params_str = ", ".join(params) if params else ""
        
        # Build the function dynamically
        func_code = f"""
def {tool_name}({params_str}):
    \"\"\"{ tool_schema.description if tool_schema else f'Call {tool_name} tool'}\"\"\"
    if not hasattr(adapter, '_loop') or not adapter._loop:
        raise RuntimeError("MCP Adapter not started")
    
    # Build kwargs from parameters
    kwargs = {{{", ".join([f"'{p.split(':')[0].strip()}': {p.split(':')[0].strip()}" for p in params])}}}
    
    # Execute on the specific loop where MCP is running
    import asyncio
    future = asyncio.run_coroutine_threadsafe(
        adapter.call_tool('{tool_name}', kwargs), 
        adapter._loop
    )
    return future.result()
"""
        
        # Execute the function definition
        namespace = {'adapter': self}
        exec(func_code, namespace)
        
        return namespace[tool_name]
