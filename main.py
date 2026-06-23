import streamlit as st
import asyncio
import os
import sys
from datetime import datetime
import pandas as pd

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db_operations import (
    init_db, create_user, get_user, list_courses, 
    list_materials, list_deadlines, list_study_groups,
    get_popular_materials, get_analytics, increment_material_popularity
)
from app.utils.security import hash_password, verify_password, validate_username
from app.agents.router_agent import router_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Page configuration
st.set_page_config(
    page_title="University Chatbot Agent Hub",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize databases on load
try:
    init_db()
except Exception as e:
    st.error(f"Failed to initialize SQLite database: {e}")

# Load environment configurations
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Styling injection for premium glassmorphic UI
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0E1117;
        color: #F0F2F6;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    /* Headers styling */
    h1, h2, h3 {
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 20px;
    }
    
    /* Card containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        margin-bottom: 20px;
    }
    
    .sidebar .sidebar-content {
        background: #161B22;
    }
    
    /* Chat styling */
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 20px;
        margin-bottom: 12px;
        max-width: 80%;
        line-height: 1.5;
        font-size: 15px;
    }
    
    .chat-user {
        background-color: #2563EB;
        color: white;
        align-self: flex-end;
        margin-left: auto;
        border-top-right-radius: 4px;
    }
    
    .chat-agent {
        background-color: #1F2937;
        color: #E5E7EB;
        align-self: flex-start;
        margin-right: auto;
        border-top-left-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Custom button styling */
    .stButton>button {
        background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%);
        color: white;
        border: none;
        padding: 8px 20px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "user" not in st.session_state:
    st.session_state.user = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"sess_{int(datetime.now().timestamp())}"
if "session_service" not in st.session_state:
    st.session_state.session_service = InMemorySessionService()

# Run async tasks inside sync Streamlit code
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# Sidebar user authentication
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/graduation-cap.png", width=70)
    st.markdown("## University Hub Authentication")
    
    if st.session_state.user is None:
        auth_mode = st.radio("Access Mode", ["Login", "Sign Up"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if auth_mode == "Sign Up":
            role = st.selectbox("Role", ["student", "professor"])
            if st.button("Register Account"):
                if not validate_username(username):
                    st.error("Username must be alphanumeric, length 3-20.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    existing = get_user(username)
                    if existing:
                        st.error("Username already registered.")
                    else:
                        hashed = hash_password(password)
                        user_id = create_user(username, hashed, role)
                        if user_id:
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Failed to create user.")
        else:
            if st.button("Login"):
                user = get_user(username)
                if user and verify_password(password, user["password_hash"]):
                    st.session_state.user = user
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    else:
        st.markdown(f"### Logged in as: **{st.session_state.user['username']}**")
        st.markdown(f"Role: `{st.session_state.user['role'].upper()}`")
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.chat_history = []
            st.rerun()

    # Diagnostic info
    st.divider()
    st.markdown("### System Diagnostics")
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
        st.success("Gemini API: Connected")
    else:
        st.warning("Gemini API: Offline / Mock Mode")

# Main Page Layout
st.markdown("<h1>🎓 University Chatbot Agent Hub</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1em; color: #9CA3AF;'>Kaggle AI Agents Capstone Hackathon - Agents for Good Track</p>", unsafe_allow_html=True)

# Main App Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Chat Agent", 
    "📤 Upload Materials", 
    "📅 Deadlines & Peer Groups", 
    "📊 Analytics Dashboard"
])

# TAB 1: Chatbot Agent
with tab1:
    st.markdown("<div class='glass-card'><h3>💬 Ask our University Agent</h3>"
                "<p>Search for past papers, calculus notes, check assignment dates, or locate peer study groups.</p></div>", 
                unsafe_allow_html=True)
                
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for sender, msg in st.session_state.chat_history:
            if sender == "user":
                st.markdown(f"<div class='chat-bubble chat-user'>{msg}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bubble chat-agent'>{msg}</div>", unsafe_allow_html=True)

    # Chat Input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([9, 1])
        user_message = col1.text_input("Type your message here...", placeholder="e.g. Find me study materials for CS101")
        submit_btn = col2.form_submit_row = col2.form_submit_button("Send")

    if submit_btn and user_message:
        # Append User message
        st.session_state.chat_history.append(("user", user_message))
        
        # Call Router Agent
        with st.spinner("Agent is reasoning..."):
            try:
                runner = Runner(agent=router_agent, session_service=st.session_state.session_service)
                session = run_async(st.session_state.session_service.create_session(
                    app_name="uni_hub", 
                    user_id=st.session_state.user["username"] if st.session_state.user else "anonymous",
                    session_id=st.session_state.session_id
                ))
                
                async def fetch_response():
                    final_text = ""
                    async for event in runner.run_async(
                        user_id=st.session_state.user["username"] if st.session_state.user else "anonymous",
                        session_id=session.id,
                        new_message=user_message
                    ):
                        if event.is_final_response() and event.content and event.content.parts:
                            final_text += event.content.parts[0].text
                    return final_text

                response = run_async(fetch_response())
                st.session_state.chat_history.append(("agent", response))
                st.rerun()
            except Exception as e:
                st.error(f"Error during agent reasoning: {e}")

# TAB 2: Upload Materials
with tab2:
    st.markdown("<div class='glass-card'><h3>📤 Share Study Materials</h3>"
                "<p>Help your peers! Upload lecture slides, homework reference sheets, or old exams.</p></div>", 
                unsafe_allow_html=True)
                
    if st.session_state.user is None:
        st.info("🔒 Please login or sign up in the sidebar to upload files.")
    else:
        # Fetch available courses
        courses = list_courses()
        course_options = [c["code"] for c in courses]
        
        with st.form("upload_form"):
            col1, col2 = st.columns(2)
            title = col1.text_input("Material Title", placeholder="e.g. Midterm 1 Preparation Guide")
            course_code = col1.selectbox("Course Code", course_options)
            material_type = col2.selectbox("Document Type", ["notes", "paper", "assignment"])
            uploaded_file = col2.file_uploader("Select File (.txt, .md, .pdf)", type=["txt", "md", "pdf"])
            
            submit_upload = st.form_submit_button("Index Document")
            
        if submit_upload:
            if not title or not uploaded_file:
                st.error("Please fill in the title and select a file.")
            else:
                # Save file to a temporary uploads directory
                uploads_dir = "app/database/uploads"
                os.makedirs(uploads_dir, exist_ok=True)
                temp_file_path = os.path.join(uploads_dir, uploaded_file.name)
                
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                with st.spinner("Processing and indexing document..."):
                    # Delegate upload logic using the router agent tools
                    # Running the agent via the runner
                    try:
                        runner = Runner(agent=router_agent, session_service=st.session_state.session_service)
                        session = run_async(st.session_state.session_service.create_session(
                            app_name="uni_hub", 
                            user_id=st.session_state.user["username"],
                            session_id=st.session_state.session_id + "_upload"
                        ))
                        
                        # Generate routing upload query instruction
                        upload_instruction = (
                            f"Index the uploaded material titled '{title}' located at '{temp_file_path}' "
                            f"for course code '{course_code}', material type '{material_type}', "
                            f"uploaded by '{st.session_state.user['username']}'."
                        )
                        
                        async def run_upload_flow():
                            final_text = ""
                            async for event in runner.run_async(
                                user_id=st.session_state.user["username"],
                                session_id=session.id,
                                new_message=upload_instruction
                            ):
                                if event.is_final_response() and event.content and event.content.parts:
                                    final_text += event.content.parts[0].text
                            return final_text

                        upload_response = run_async(run_upload_flow())
                        
                        if "Success" in upload_response:
                            st.success(upload_response)
                        else:
                            st.info(upload_response)
                    except Exception as e:
                        st.error(f"Failed to register material: {e}")

# TAB 3: Deadlines & Peer Groups
with tab3:
    st.markdown("<div class='glass-card'><h3>📅 Deadlines & 👥 Peer Study Groups</h3>"
                "<p>Add and view upcoming homework deadlines or join local subject study cohorts.</p></div>", 
                unsafe_allow_html=True)
                
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add Assignment Deadline")
        if st.session_state.user is None:
            st.info("🔒 Login to schedule reminders.")
        else:
            courses = list_courses()
            course_codes = [c["code"] for c in courses]
            
            with st.form("deadline_form"):
                d_title = st.text_input("Assignment Title", placeholder="e.g. Problem Set 3")
                d_course = st.selectbox("Course", course_codes, key="d_c")
                d_date = st.date_input("Due Date")
                submit_deadline = st.form_submit_button("Save Reminder")
                
            if submit_deadline and d_title:
                try:
                    runner = Runner(agent=router_agent, session_service=st.session_state.session_service)
                    session = run_async(st.session_state.session_service.create_session(
                        app_name="uni_hub", 
                        user_id=st.session_state.user["username"],
                        session_id=st.session_state.session_id + "_deadline"
                    ))
                    
                    deadline_instruction = (
                        f"Create an assignment reminder titled '{d_title}' due on '{d_date}' "
                        f"for course '{d_course}'."
                    )
                    
                    async def run_deadline_flow():
                        final_text = ""
                        async for event in runner.run_async(
                            user_id=st.session_state.user["username"],
                            session_id=session.id,
                            new_message=deadline_instruction
                        ):
                            if event.is_final_response() and event.content and event.content.parts:
                                final_text += event.content.parts[0].text
                        return final_text

                    dl_response = run_async(run_deadline_flow())
                    st.success(dl_response)
                except Exception as e:
                    st.error(f"Error adding deadline: {e}")

        # List deadlines
        st.subheader("Upcoming Deadlines Calendar")
        try:
            deadlines = list_deadlines()
            if not deadlines:
                st.write("No upcoming deadlines cataloged.")
            else:
                df_dl = pd.DataFrame(deadlines)
                st.table(df_dl[["course_code", "title", "due_date"]])
        except Exception as e:
            st.write("Catalog empty or failed loading.")
            
    with col2:
        st.subheader("Register Peer Study Group")
        if st.session_state.user is None:
            st.info("🔒 Login to join groups.")
        else:
            courses = list_courses()
            course_codes = [c["code"] for c in courses]
            
            with st.form("group_form"):
                g_name = st.text_input("Group Name", placeholder="e.g. Calculus Midterm Study Cohort")
                g_course = st.selectbox("Course", course_codes, key="g_c")
                g_meeting = st.text_input("Meeting Details", placeholder="e.g. Tuesdays 5PM in Library basement or Zoom URL")
                submit_group = st.form_submit_button("Register Study Group")
                
            if submit_group and g_name and g_meeting:
                try:
                    runner = Runner(agent=router_agent, session_service=st.session_state.session_service)
                    session = run_async(st.session_state.session_service.create_session(
                        app_name="uni_hub", 
                        user_id=st.session_state.user["username"],
                        session_id=st.session_state.session_id + "_group"
                    ))
                    
                    group_instruction = (
                        f"Register a study group named '{g_name}' meeting at '{g_meeting}' "
                        f"for course '{g_course}'."
                    )
                    
                    async def run_group_flow():
                        final_text = ""
                        async for event in runner.run_async(
                            user_id=st.session_state.user["username"],
                            session_id=session.id,
                            new_message=group_instruction
                        ):
                            if event.is_final_response() and event.content and event.content.parts:
                                final_text += event.content.parts[0].text
                        return final_text

                    g_response = run_async(run_group_flow())
                    st.success(g_response)
                except Exception as e:
                    st.error(f"Error registering group: {e}")

        # List Study Groups
        st.subheader("Active Peer Groups")
        try:
            groups = list_study_groups()
            if not groups:
                st.write("No peer groups registered yet.")
            else:
                df_g = pd.DataFrame(groups)
                st.table(df_g[["course_code", "group_name", "meeting_info"]])
        except Exception as e:
            st.write("Catalog empty or failed loading.")

# TAB 4: Analytics Dashboard
with tab4:
    st.markdown("<div class='glass-card'><h3>📊 Analytics Dashboard</h3>"
                "<p>Explore trending files, course content counts, and popular questions students are asking.</p></div>", 
                unsafe_allow_html=True)
                
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Trending Study Materials")
        try:
            pop_materials = get_popular_materials(limit=5)
            if not pop_materials:
                st.info("No clicks or popularity data logged yet.")
            else:
                df_pop = pd.DataFrame(pop_materials)
                st.bar_chart(data=df_pop, x="title", y="popular_score", color="#3B82F6")
                
                # Interactive click simulator for demo
                st.markdown("#### Simulate Click to view (increments popularity)")
                for idx, row in df_pop.iterrows():
                    if st.button(f"👁️ View {row['title']} ({row['course_code']})", key=f"click_{row['id']}"):
                        increment_material_popularity(row['id'])
                        st.success(f"Incremented popular score for {row['title']}!")
                        st.rerun()
        except Exception as e:
            st.error(f"Failed loading analytics: {e}")
            
    with col2:
        st.subheader("🔍 Frequently Asked Search Queries")
        try:
            queries = get_analytics(limit=5)
            if not queries:
                st.info("No search query logs recorded yet.")
            else:
                df_q = pd.DataFrame(queries)
                st.bar_chart(data=df_q, x="query", y="total_count", color="#06B6D4")
        except Exception as e:
            st.error(f"Failed loading query analytics: {e}")
            
    # Course catalog list
    st.divider()
    st.subheader("📚 Register of active Courses")
    try:
        courses = list_courses()
        all_mats = list_materials()
        df_courses = pd.DataFrame(courses)
        
        # Calculate materials count per course
        count_dict = {c["code"]: 0 for c in courses}
        for m in all_mats:
            if m["course_code"] in count_dict:
                count_dict[m["course_code"]] += 1
                
        df_courses["materials_count"] = df_courses["code"].map(count_dict)
        st.dataframe(df_courses[["code", "name", "materials_count"]], use_container_width=True)
    except Exception as e:
        st.write("No courses logged.")
