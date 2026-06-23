import os
from pypdf import PdfReader

def extract_text_from_file(file_path: str) -> str:
    """Extracts raw text content from TXT, MD, or PDF documents."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    _, ext = os.path.splitext(file_path.lower())
    
    if ext in ('.txt', '.md'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 if utf-8 fails
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
                
    elif ext == '.pdf':
        try:
            reader = PdfReader(file_path)
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n--- Page Break ---\n\n".join(text_parts)
        except Exception as e:
            raise IOError(f"Failed to read PDF file: {str(e)}")
            
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only PDF, TXT, and MD are supported.")
