from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
import asyncio
import uuid

import threading

def run_agent_sync(agent_factory, prompt: str) -> str:
    """
    Runs a Google ADK Agent synchronously using InMemoryRunner.
    Safely handles extraction of the response text.
    Executes in a separate thread to avoid nested asyncio loop conflicts.
    Takes an agent_factory callable to create the agent on the correct thread.
    """
    result_container = {"text": "", "error": None}

    def target():
        # Create agent INSIDE the thread to ensure thread-affinity of async clients
        agent = agent_factory()
        
        # Initialize Runner with correct app_name
        enhanced_runner = InMemoryRunner(agent=agent, app_name="agents")
        
        # Create session
        session_id = str(uuid.uuid4())
        async def setup_session():
            return await enhanced_runner.session_service.create_session(
                user_id="user", 
                session_id=session_id, 
                app_name="agents"
            )
        
        try:
            # This is safe because we are in a new thread
            asyncio.run(setup_session())
            
            # Prepare message
            message = Content(parts=[Part(text=prompt)], role="user")
            
            # Run agent
            for event in enhanced_runner.run(user_id="user", session_id=session_id, new_message=message):
                if hasattr(event, 'response') and event.response:
                    try:
                        text = event.response.text
                        if text:
                            result_container["text"] = text
                    except Exception:
                        pass
                elif hasattr(event, 'content') and event.content:
                     try:
                        if hasattr(event.content, 'parts'):
                            parts = event.content.parts
                            text_parts = [p.text for p in parts if hasattr(p, 'text') and p.text]
                            if text_parts:
                                result_container["text"] = "\n".join(text_parts)
                     except Exception:
                        pass
        except Exception as e:
            result_container["error"] = e
            # Log error but don't crash
            # print(f"run_agent_sync error: {e}")

    t = threading.Thread(target=target)
    t.start()
    t.join() # Wait for the thread to complete
    
    if result_container["error"]:
        return f"Agent Run Failed: {result_container['error']}"
    
    return result_container["text"]
