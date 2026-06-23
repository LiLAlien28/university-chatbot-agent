import os
import sys
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Ensure root directory in path for relative imports if run as main
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Find the path to the upload MCP server relative to this script
mcp_server_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "upload_mcp.py")
)

# Initialize the Upload/Registration Specialist Agent
# It is equipped with the upload_mcp.py tools to record deadlines, index uploads, and assign groups.
upload_agent = Agent(
    name="upload_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Upload & Registration Specialist Agent for the University Chatbot. "
        "Your task is to catalog newly uploaded study files (notes, exams, assignments) in ChromaDB and SQLite, "
        "record homework or exam deadlines, and coordinate peer study groups. "
        "Before calling your tools, ensure you have all required parameters (such as uploader username, "
        "course code, deadlines, or meeting schedules). If any data is missing, ask the user politely for details. "
        "Confirm successful registrations in a helpful and clean format."
    ),
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="py",
                args=[mcp_server_path]
            )
        )
    ]
)

if __name__ == "__main__":
    # Diagnostic interactive run
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    import asyncio
    
    async def main():
        session_service = InMemorySessionService()
        runner = Runner(agent=upload_agent, session_service=session_service)
        session = await session_service.create_session("app", "test_user", "test_session")
        print("Upload Agent ready. Enter request:")
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() in ("exit", "quit"):
                    break
                async for event in runner.run_async("test_user", session.id, user_input):
                    if event.is_final_response() and event.content and event.content.parts:
                        print(event.content.parts[0].text)
            except KeyboardInterrupt:
                break
                
    asyncio.run(main())
