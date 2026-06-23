# 🎓 University Chatbot Agent - Kaggle AI Agents Capstone Hackathon

A specialized multi-agent assistant built for the **"Agents for Good"** track of the Kaggle AI Agents Capstone Hackathon. This application helps university students find study notes, assignments, and past papers semantically, while enabling features like homework reminders, peer study groups, and usage analytics.

---

## 🏗️ Architectural Design

The chatbot uses a multi-agent routing system built on top of the **Google Agent Development Kit (ADK)** and the **Model Context Protocol (MCP)**.

```
       [ Streamlit Web App ]
                 │
                 ▼
       [ ADK Router Agent ]
        /        │        \
       /         │         \
      ▼          ▼          ▼
[ Search ]   [ Upload ]  [ Recs ]   <── (ADK Specialist Agents)
   Agent       Agent      Agent
     │           │          │
     ▼           ▼          ▼
 [Search]    [Upload]     [DB]      <── (MCP Servers / local database)
   MCP          MCP     Operations
  Server       Server       │
  (sqlite,    (sqlite,      ▼
  chroma)     chroma)    [SQLite DB]
```

1. **Supervisory Orchestrator (Router Agent)**: An ADK agent that understands the user's intent and delegates workflows via tool calls to specialized sub-agents.
2. **Search Specialist Agent**: Connected to the `Search MCP Server` using ADK's native `MCPToolset`. It performs semantic query vector matching in ChromaDB and catalog lookups in SQLite.
3. **Upload & Indexing Agent**: Connected to the `Upload MCP Server` via `MCPToolset`. It extracts raw text from uploads (.txt, .pdf, .md), registers metadata in SQLite, and computes/stores vector embeddings in ChromaDB.
4. **Smart Recommendation Agent**: An ADK agent equipped with database querying capabilities to suggest supplementary notes and papers based on what a student is studying.

---

## 🛠️ Technology Stack

- **Framework**: Google ADK (Agent Development Kit) 2.0+
- **Model Context Protocol**: FastMCP (Python)
- **Vector Search**: ChromaDB
- **Database**: SQLite
- **LLM / Embeddings**: Google Gemini API (`gemini-2.5-flash` & `text-embedding-004`)
- **Frontend Dashboard**: Streamlit

---

## 🔐 Security & Hackathon Best Practices

- **Zero API Key Leakage**: No API keys are committed in source code. All configuration values are loaded from a secure local `.env` environment file.
- **User Authentication**: Encrypted password storage using `bcrypt` prevents unauthorized access to features like study material uploads, peer group registration, and homework scheduling.
- **Offline / Local Sandbox Fallback**: Generates mock vector embeddings if `GEMINI_API_KEY` is not present, allowing review panel execution offline without system failures.

---

## 🚀 Setup & Execution

### 1. Prerequisites
Ensure you have **Python 3.10+** (Python 3.14 recommended) and `pip` installed.

### 2. Installation
Clone the repository and install dependencies:
```bash
py -m pip install -r requirements.txt
```

### 3. Environment Configuration
Create or configure the `.env` file in the project root:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
SQLITE_DB_PATH=app/database/university_chatbot.db
CHROMADB_DIR=app/database/chroma_db
```

### 4. Running the Application Locally
Launch the Streamlit web dashboard:
```bash
streamlit run app/main.py
```

Open your browser and navigate to **`http://localhost:8501`**.

---

## 🧪 Testing and Verification

To verify modules are functioning correctly, you can run diagnostic tests:
- **Database Verification**:
  ```bash
  py -c "from app.database.db_operations import init_db; init_db()"
  ```
- **Vector Store Verification**:
  ```bash
  py -c "from app.tools.vector_store import test_chroma; test_chroma()"
  ```
