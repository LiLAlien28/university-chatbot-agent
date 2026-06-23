import sys
import os
from mcp.server.fastmcp import FastMCP

# Add root directory to python path for local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.db_operations import list_materials, list_courses, get_popular_materials, log_analytics
from app.tools.vector_store import VectorStoreManager

# Initialize FastMCP Server
mcp = FastMCP("Search MCP Server")

try:
    vector_store = VectorStoreManager()
except Exception as e:
    print(f"Warning: Failed to init vector store: {e}")
    vector_store = None

@mcp.tool()
def search_study_materials(query: str, course_code: str = None) -> str:
    """Search study materials semantically using ChromaDB and SQL matches.
    
    Args:
        query: The search query string.
        course_code: Optional course code filter (e.g. CS101).
    """
    # Log the search query in analytics
    try:
        log_analytics(query=query)
    except Exception as e:
        print(f"Error logging analytics: {e}")
        
    results = []
    
    # 1. Semantic Search
    results.append("### Semantic Search Results (ChromaDB):")
    if vector_store:
        try:
            semantic_matches = vector_store.search_materials(query, course_code=course_code, limit=4)
            if not semantic_matches:
                results.append("No semantically matching files found.")
            else:
                for match in semantic_matches:
                    results.append(
                        f"- **{match['title']}** ({match['material_type'].upper()}) for course {match['course_code']}\n"
                        f"  *Snippet:* {match['content_snippet']}\n"
                        f"  *Uploader:* {match['uploader']}"
                    )
        except Exception as e:
            results.append(f"Error performing semantic search: {str(e)}")
    else:
        results.append("Semantic search is unavailable (Vector store initialization failed).")

    # 2. Database Catalog Search
    results.append("\n### Database Catalog Matches (SQLite):")
    try:
        db_matches = list_materials(course_code=course_code, keyword=query)
        if not db_matches:
            results.append("No catalog matches found in database.")
        else:
            for item in db_matches:
                results.append(
                    f"- **{item['title']}** ({item['material_type'].upper()}) - Course: {item['course_code']} "
                    f"| Uploader: {item['uploader']} | Popularity: {item['popular_score']}"
                )
    except Exception as e:
        results.append(f"Error querying database catalog: {str(e)}")
        
    return "\n".join(results)

@mcp.tool()
def list_available_courses() -> str:
    """Retrieves all registered university courses from the catalog."""
    try:
        courses = list_courses()
        if not courses:
            return "No courses found."
        formatted = ["### Registered University Courses:"]
        for c in courses:
            formatted.append(f"- **{c['code']}**: {c['name']} - *{c['description']}*")
        return "\n".join(formatted)
    except Exception as e:
        return f"Error listing courses: {str(e)}"

@mcp.tool()
def show_popular_materials() -> str:
    """Lists the top most popular materials based on clicks/views."""
    try:
        materials = get_popular_materials(limit=5)
        if not materials:
            return "No popular materials registered yet."
        formatted = ["### Popular Study Materials:"]
        for m in materials:
            formatted.append(
                f"- **{m['title']}** ({m['material_type'].upper()}) - Course: {m['course_code']} "
                f"(Popularity Score: {m['popular_score']})"
            )
        return "\n".join(formatted)
    except Exception as e:
        return f"Error retrieving popular materials: {str(e)}"

if __name__ == "__main__":
    mcp.run()
