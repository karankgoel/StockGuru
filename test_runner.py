import os
import asyncio
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

if "GOOGLE_API_KEY" not in os.environ:
    print("Please set GOOGLE_API_KEY")
    exit(1)

agent = Agent(name="test", model="gemini-pro", instruction="Say hello")
session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name="test_app", session_service=session_service)

async def setup_session():
    return await session_service.create_session(user_id="test_user", session_id="test_session", app_name="test_app")

# Create session
session = asyncio.run(setup_session())
print(f"Session Dir: {dir(session)}")
# print(f"Created session: {session.session_id}")

print("Running agent...")
message = Content(parts=[Part(text="Hi")], role="user")

for event in runner.run(user_id="test_user", session_id="test_session", new_message=message):
    if hasattr(event, 'response'):
        if hasattr(event.response, 'text'):
            print(f"Response Text: {event.response.text}")
