import sys
import os
from mcp.server.fastmcp import FastMCP

# Add root directory to python path for local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.db_operations import (
    add_material, add_deadline, list_deadlines, 
    add_study_group, list_study_groups, get_user
)
from app.tools.file_processor import extract_text_from_file
from app.tools.vector_store import VectorStoreManager

# Initialize FastMCP Server
mcp = FastMCP("Upload MCP Server")

try:
    vector_store = VectorStoreManager()
except Exception as e:
    print(f"Warning: Failed to init vector store in Upload MCP: {e}")
    vector_store = None

@mcp.tool()
def index_uploaded_material(title: str, file_path: str, course_code: str, material_type: str, uploader_username: str) -> str:
    """Extracts content from a file and indexes it in both SQLite database and ChromaDB.
    
    Args:
        title: The title of the study material (e.g. 'Calculus Lecture 1 Notes').
        file_path: The absolute/relative path to the uploaded file on disk.
        course_code: The course identifier (e.g. 'CS101').
        material_type: Must be 'notes', 'paper', or 'assignment'.
        uploader_username: The username of the student or professor uploading it.
    """
    # Verify uploader
    user = get_user(uploader_username)
    if not user:
        return f"Error: User '{uploader_username}' does not exist. Please register first."
        
    uploader_id = user["id"]
    
    if material_type not in ('notes', 'paper', 'assignment'):
        return "Error: material_type must be one of 'notes', 'paper', or 'assignment'."
        
    if not os.path.exists(file_path):
        return f"Error: Uploaded file not found at path '{file_path}'."
        
    try:
        # 1. Parse content
        content = extract_text_from_file(file_path)
    except Exception as e:
        return f"Error: Failed to process/parse document: {str(e)}"
        
    try:
        # 2. Save metadata to SQLite
        material_id = add_material(
            title=title,
            file_path=file_path,
            course_code=course_code,
            uploader_id=uploader_id,
            material_type=material_type
        )
        
        # 3. Add to ChromaDB vector store for semantic search
        if vector_store:
            vector_store.add_material(
                material_id=material_id,
                title=title,
                content=content,
                course_code=course_code,
                material_type=material_type,
                uploader=uploader_username
            )
            vector_message = "and successfully indexed in the vector store for semantic search."
        else:
            vector_message = "but vector indexing failed (vector store unavailable)."
            
        return f"Success: Material '{title}' has been cataloged in SQLite (ID: {material_id}) {vector_message}"
    except Exception as e:
        return f"Error registering material in database: {str(e)}"

@mcp.tool()
def create_assignment_reminder(title: str, due_date: str, course_code: str) -> str:
    """Adds a new assignment deadline to the database.
    
    Args:
        title: Title/name of the assignment.
        due_date: The deadline date (YYYY-MM-DD format).
        course_code: The corresponding course code (e.g. 'CS101').
    """
    try:
        deadline_id = add_deadline(title, due_date, course_code)
        return f"Success: Reminder for '{title}' created under course {course_code} (ID: {deadline_id}, Due: {due_date})."
    except Exception as e:
        return f"Error creating reminder: {str(e)}"

@mcp.tool()
def get_deadlines(course_code: str = None) -> str:
    """Fetches upcoming deadlines, optionally filtered by course_code."""
    try:
        deadlines = list_deadlines(course_code)
        if not deadlines:
            return "No upcoming assignment deadlines found."
        formatted = ["### Upcoming Assignment Deadlines:"]
        for d in deadlines:
            formatted.append(f"- **[{d['course_code']}] {d['title']}** | Due Date: {d['due_date']}")
        return "\n".join(formatted)
    except Exception as e:
        return f"Error fetching deadlines: {str(e)}"

@mcp.tool()
def register_study_group(course_code: str, group_name: str, meeting_info: str) -> str:
    """Creates a peer study group for a course.
    
    Args:
        course_code: The course code (e.g. 'MATH101').
        group_name: The name of the study group.
        meeting_info: Details about when and where they meet (e.g. 'Mondays 5PM at Library Room 3A' or Zoom link).
    """
    try:
        group_id = add_study_group(course_code, group_name, meeting_info)
        return f"Success: Study group '{group_name}' registered for course {course_code} (ID: {group_id})."
    except Exception as e:
        return f"Error registering study group: {str(e)}"

@mcp.tool()
def show_study_groups(course_code: str = None) -> str:
    """Lists study groups, optionally filtered by course_code."""
    try:
        groups = list_study_groups(course_code)
        if not groups:
            return "No study groups found for the specified criteria."
        formatted = ["### Active Peer Study Groups:"]
        for g in groups:
            formatted.append(f"- **[{g['course_code']}] {g['group_name']}** | Meeting Info: {g['meeting_info']}")
        return "\n".join(formatted)
    except Exception as e:
        return f"Error fetching study groups: {str(e)}"

if __name__ == "__main__":
    mcp.run()
