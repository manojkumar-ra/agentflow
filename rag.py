import os
import chromadb
from chromadb.utils import embedding_functions

# vector db gets stored here
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "documents"

# NOTE: first time you run this it downloads the embedding model (~80mb)
# after that its cached so dont worry
_client = None
_collection = None


def get_collection():
    global _client, _collection

    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)

        # this model converts text into vectors for similarity search
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    return _collection


def chunk_text(text, chunk_size=500, overlap=50):
    """split text into smaller pieces so the vector search works better
    the overlap part makes sure we dont lose context at the edges"""
    chunks = []
    words = text.split()

    if len(words) <= chunk_size:
        return [text]

    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap

    return chunks


def extract_text_from_file(file_path, filename):
    """pulls text out of different file formats - pdf, docx, txt etc"""
    ext = filename.lower().split('.')[-1]

    if ext == "txt":
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    elif ext == "pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            print(f"pdf error: {e}")
            return ""

    elif ext == "docx":
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            print(f"docx error: {e}")
            return ""

    elif ext in ["md", "csv", "json", "py", "js", "html"]:
        # plain text files
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    else:
        return ""


def add_document(text, filename, doc_id=None):
    """takes text, breaks it into chunks, and stores in chromadb"""
    collection = get_collection()

    if not text or len(text.strip()) < 10:
        return {"error": "document is too short or empty"}

    chunks = chunk_text(text)
    print(f"adding {len(chunks)} chunks from {filename}")

    # create unique ids for each chunk
    base_id = doc_id or filename.replace(" ", "_").replace(".", "_")

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"{base_id}_chunk_{i}"
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({
            "filename": filename,
            "chunk_index": i,
            "total_chunks": len(chunks)
        })

    # add to chromadb
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    return {
        "filename": filename,
        "chunks": len(chunks),
        "total_chars": len(text)
    }


def search_documents(query, top_k=5):
    """this is the main RAG function - finds relevant text chunks for a query"""
    collection = get_collection()

    # check if we have any documents
    if collection.count() == 0:
        return "No documents uploaded yet. Please upload some documents first."

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count())
    )

    if not results['documents'] or not results['documents'][0]:
        return "No relevant information found in the uploaded documents."

    # put results together in a readable format
    output = ""
    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        # cosine distance - lower is more similar
        score = round(1 - dist, 3)
        output += f"\n--- From: {meta['filename']} (relevance: {score}) ---\n"
        output += doc.strip() + "\n"

    return output.strip()


def get_doc_count():
    """how many chunks are in the vector db"""
    try:
        collection = get_collection()
        return collection.count()
    except:
        return 0


def get_uploaded_files():
    """returns all the file names that have been uploaded"""
    try:
        collection = get_collection()
        if collection.count() == 0:
            return []

        # get all metadatas to find unique filenames
        all_data = collection.get()
        filenames = set()
        for meta in all_data['metadatas']:
            filenames.add(meta.get('filename', 'unknown'))

        return list(filenames)
    except:
        return []


def delete_document(filename):
    """delete all chunks for a specific document"""
    try:
        collection = get_collection()
        # find all chunks with this filename
        all_data = collection.get(where={"filename": filename})

        if all_data['ids']:
            collection.delete(ids=all_data['ids'])
            return True
        return False
    except Exception as e:
        print(f"delete error: {e}")
        return False
