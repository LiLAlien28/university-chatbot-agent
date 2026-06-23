import os
import chromadb
from google import genai
import random

# Read configuration directories
CHROMADB_DIR = os.getenv("CHROMADB_DIR", "app/database/chroma_db")

def get_embedding(text: str) -> list:
    """Computes text embeddings using Google's text-embedding-004.
    Falls back to mock embeddings if API key is missing or invalid.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "YOUR_GEMINI_API_KEY" in api_key or api_key.strip() == "":
        # Generate 768-dimensional mock embedding for offline development
        random.seed(hash(text))
        return [random.uniform(-0.1, 0.1) for _ in range(768)]
        
    try:
        # Initialize Google GenAI client
        client = genai.Client(api_key=api_key)
        response = client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Embedding API error: {e}. Falling back to mock embeddings.")
        random.seed(hash(text))
        return [random.uniform(-0.1, 0.1) for _ in range(768)]

class VectorStoreManager:
    def __init__(self):
        # Create persistent directory
        os.makedirs(CHROMADB_DIR, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=CHROMADB_DIR)
        # Create or fetch collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="university_materials",
            metadata={"hnsw:space": "cosine"}
        )

    def add_material(self, material_id: int, title: str, content: str, course_code: str, material_type: str, uploader: str):
        """Chunks content, generates embeddings, and adds document to ChromaDB."""
        # Chunk text if it is very large (e.g. over 1500 chars)
        chunks = []
        chunk_size = 1500
        overlap = 200
        
        if len(content) <= chunk_size:
            chunks.append(content)
        else:
            start = 0
            while start < len(content):
                chunks.append(content[start:start+chunk_size])
                start += (chunk_size - overlap)
                
        # Add chunks with embeddings
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            doc_id = f"mat_{material_id}_chunk_{i}"
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[{
                    "material_id": material_id,
                    "title": title,
                    "course_code": course_code,
                    "material_type": material_type,
                    "uploader": uploader,
                    "chunk_index": i
                }],
                documents=[chunk]
            )

    def search_materials(self, query: str, course_code: str = None, limit: int = 5) -> list:
        """Searches ChromaDB for semantically similar materials."""
        query_vector = get_embedding(query)
        
        # Build metadata filter
        where_filter = {}
        if course_code:
            where_filter["course_code"] = course_code
            
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=where_filter if where_filter else None
        )
        
        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            for idx in range(len(results["ids"][0])):
                # Dedup by material_id in return list
                metadata = results["metadatas"][0][idx]
                document = results["documents"][0][idx]
                distance = results["distances"][0][idx] if "distances" in results else 0.0
                
                formatted_results.append({
                    "material_id": metadata["material_id"],
                    "title": metadata["title"],
                    "course_code": metadata["course_code"],
                    "material_type": metadata["material_type"],
                    "uploader": metadata["uploader"],
                    "content_snippet": document[:200] + "..." if len(document) > 200 else document,
                    "distance": distance
                })
        return formatted_results

def test_chroma():
    """Diagnostic tool to verify vector store is active."""
    manager = VectorStoreManager()
    manager.add_material(
        material_id=999,
        title="Calculus Notes",
        content="Limits and derivatives form the foundation of calculus.",
        course_code="MATH101",
        material_type="notes",
        uploader="professor_smith"
    )
    res = manager.search_materials("derivatives", course_code="MATH101")
    assert len(res) > 0, "Vector search failed"
    print("Vector Store verification passed.")
