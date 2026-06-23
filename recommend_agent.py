import sys
import os
from google.adk.agents import Agent

# Ensure root directory in path for relative imports if run as main
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.db_operations import list_materials

def recommend_related_materials(current_material_title: str, course_code: str) -> str:
    """Suggests related study materials based on the active course and title context.
    
    Args:
        current_material_title: The title of the material currently being viewed.
        course_code: The course code of the material currently being viewed (e.g. CS101).
    """
    try:
        # Fetch materials in the same course
        all_materials = list_materials(course_code=course_code)
        # Filter out current material
        related = [m for m in all_materials if m["title"].lower() != current_material_title.lower()]
        
        if not related:
            return f"No other materials found for course '{course_code}' yet."
            
        res = [f"Recommended materials in course {course_code}:"]
        # Limit to top 3 recommendations
        for r in related[:3]: 
            res.append(f"- **{r['title']}** ({r['material_type'].upper()}) - Uploader: {r['uploader']}")
        return "\n".join(res)
    except Exception as e:
        return f"Error retrieving recommendations: {str(e)}"

# Initialize the Recommendation Specialist Agent
recommend_agent = Agent(
    name="recommend_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Smart Recommendation Specialist Agent for the University Chatbot. "
        "Your goal is to suggest related materials to students based on the material they are currently viewing. "
        "Use the recommend_related_materials tool to find relevant matches. "
        "Always state the course code and title, and explain in a sentence why these resources "
        "might be helpful (e.g., matching subject, extra practice exams)."
    ),
    tools=[recommend_related_materials]
)

if __name__ == "__main__":
    # Diagnostic interactive run
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    import asyncio
    
    async def main():
        session_service = InMemorySessionService()
        runner = Runner(agent=recommend_agent, session_service=session_service)
        session = await session_service.create_session("app", "test_user", "test_session")
        print("Recommendation Agent ready. Enter course code and file title:")
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
