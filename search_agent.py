import os
import sys
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Ensure root directory in path for relative imports if run as main
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Find the path to the search MCP server relative to this script
mcp_server_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "search_mcp.py")
)

# Initialize the Search Specialist Agent
# It is equipped with the search_mcp.py tools via standard MCP Client transport
search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Search Specialist Agent for the University Chatbot. "
        "Your task is to search for study materials, exam past papers, and lecture notes "
        "using your search tools. You can also list available courses or popular files. "
        "When the user requests files for a specific class or topic, call search_study_materials. "
        "Return the search results to the student in a clear, formatted markdown block, "
        "highlighting the course, title, and who uploaded it."
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
    # If run directly, start an interactive loop for diagnostics
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    import asyncio
    
    async def main():
        session_service = InMemorySessionService()
        runner = Runner(agent=search_agent, session_service=session_service)
        session = await session_service.create_session("app", "test_user", "test_session")
        print("Search Agent ready. Enter query:")
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
