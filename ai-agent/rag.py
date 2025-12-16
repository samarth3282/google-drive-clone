import os
import pdfplumber
import io
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.id import ID
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.tools import tool
from typing import Optional, Dict, Any, List, Tuple
import os
import asyncio
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
from collections import Counter
import math
from datetime import datetime

from error_handling import (
    handle_tool_error,
    safe_appwrite_call,
    ValidationError,
    logger
)
from cache import vector_cache, cached

load_dotenv(dotenv_path="../.env.local")

# Constants
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CHUNKS_TO_INDEX = 50  # Increased from 10 to allow more content
MIN_TEXT_LENGTH = 100
MAX_VECTOR_RESULTS = 1000
MAX_USER_FILES = 1000
TOP_CHUNKS_RETURNED = 5  # Increased from 3 for better context
OCR_RETRY_MAX_ATTEMPTS = 3
OCR_RETRY_BASE_DELAY = 10  # seconds

# Hybrid search constants
SEMANTIC_WEIGHT = 0.7  # Weight for semantic similarity
KEYWORD_WEIGHT = 0.3   # Weight for keyword matching (BM25)
BM25_K1 = 1.5          # BM25 parameter
BM25_B = 0.75          # BM25 parameter

# Helper function to get user context from environment
def get_user_context() -> Dict[str, str]:
    """Extract user context from environment variables set by agent."""
    return {
        "userId": os.environ.get("_CURRENT_USER_ID", ""),
        "userEmail": os.environ.get("_CURRENT_USER_EMAIL", "")
    }

ENDPOINT = os.getenv("NEXT_PUBLIC_APPWRITE_ENDPOINT")
PROJECT_ID = os.getenv("NEXT_PUBLIC_APPWRITE_PROJECT")
API_KEY = os.getenv("NEXT_APPWRITE_KEY")
DATABASE_ID = os.getenv("NEXT_PUBLIC_APPWRITE_DATABASE")
BUCKET_ID = os.getenv("NEXT_PUBLIC_APPWRITE_BUCKET")
VECTOR_COLLECTION_ID = os.getenv("NEXT_PUBLIC_APPWRITE_VECTOR_COLLECTION")
import json
import numpy as np
from appwrite.query import Query
client = Client()
client.set_endpoint(ENDPOINT)
client.set_project(PROJECT_ID)
client.set_key(API_KEY)

databases = Databases(client)
storage = Storage(client)

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

import google.generativeai as genai
import tempfile

# Configure GenAI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# BM25 Implementation for keyword search
class BM25:
    """Simple BM25 implementation for keyword-based search."""
    
    def __init__(self, documents: List[str], k1: float = BM25_K1, b: float = BM25_B):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        
        # Tokenize and compute stats
        self.doc_lengths = []
        self.doc_freqs = []
        self.idf = {}
        
        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_lengths.append(len(tokens))
            freq = Counter(tokens)
            self.doc_freqs.append(freq)
            
            # Update document frequency for IDF
            for token in set(tokens):
                self.idf[token] = self.idf.get(token, 0) + 1
        
        # Compute average document length
        self.avg_doc_len = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 0
        
        # Compute IDF scores
        for token in self.idf:
            self.idf[token] = math.log((self.doc_count - self.idf[token] + 0.5) / (self.idf[token] + 0.5) + 1)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric."""
        return re.findall(r'\w+', text.lower())
    
    def score(self, query: str, doc_idx: int) -> float:
        """Compute BM25 score for a query against a document."""
        query_tokens = self._tokenize(query)
        score = 0.0
        doc_freq = self.doc_freqs[doc_idx]
        doc_len = self.doc_lengths[doc_idx]
        
        for token in query_tokens:
            if token not in doc_freq:
                continue
            
            freq = doc_freq[token]
            idf = self.idf.get(token, 0)
            
            # BM25 formula
            numerator = freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
            score += idf * (numerator / denominator)
        
        return score
    
    def get_scores(self, query: str) -> List[float]:
        """Get BM25 scores for all documents."""
        return [self.score(query, i) for i in range(self.doc_count)]

def normalize_scores(scores: List[float]) -> List[float]:
    """Normalize scores to [0, 1] range using min-max normalization."""
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    if max_score == min_score:
        return [0.5] * len(scores)  # All equal, return mid-range
    
    return [(s - min_score) / (max_score - min_score) for s in scores]

def hybrid_score(semantic_score: float, keyword_score: float) -> float:
    """Combine semantic and keyword scores with weights."""
    return SEMANTIC_WEIGHT * semantic_score + KEYWORD_WEIGHT * keyword_score

def smart_extract_text(file_bytes: bytes, file_ext: str = ".pdf") -> str:
    """
    Extracts text using pdfplumber first. 
    If text is sparse (scanned PDF), falls back to Gemini Flash for OCR.
    """
    text = ""
    # 1. Try standard extraction
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        logger.debug(f"pdfplumber extraction failed: {e}")

    # 2. Check density. If < MIN_TEXT_LENGTH chars, assume scanned.
    if len(text.strip()) > MIN_TEXT_LENGTH:
        return text
    
    logger.info("Text sparse/empty. Falling back to Gemini OCR...")
    import time
    
    try:
        # Create temp file with context manager
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            # Upload to Gemini
            logger.info(f"Uploading {tmp_path} to Gemini for OCR...")
            myfile = genai.upload_file(tmp_path)
            logger.info(f"File uploaded to Gemini: {myfile.name}")
            
            # Generative extraction with Retry Logic
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            logger.debug("Generating OCR content with Gemini...")
            
            result_text = ""
            for attempt in range(OCR_RETRY_MAX_ATTEMPTS):
                try:
                    result = model.generate_content([myfile, "Transcribe the full text of this document verbatim."])
                    result_text = result.text
                    logger.info(f"Gemini OCR success! Extracted {len(result_text)} characters")
                    break # Success
                except Exception as e:
                    if "429" in str(e) and attempt < OCR_RETRY_MAX_ATTEMPTS - 1:
                        wait_time = (attempt + 1) * OCR_RETRY_BASE_DELAY
                        logger.warning(f"Rate limit hit during OCR. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise e # Re-raise if not 429 or last attempt
            
            return result_text
        finally:
            # Cleanup temp file even if error occurs
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            
    except Exception as e:
        logger.error(f"Gemini OCR failed: {e}")
        logger.debug(f"OCR failure traceback:", exc_info=True)
        return text # Return whatever we had

@tool
@handle_tool_error
async def process_file_for_search(file_id: str, bucket_file_id: str) -> str:
    """
    Downloads a file (PDF), extracts text, creates embeddings, and indexes it for search.
    Use this when user asks to "analyze" or "read" a specific file.
    """
    # Validate inputs
    if not file_id or len(file_id) > 100:
        return "Error: Invalid file ID"
    if not bucket_file_id or len(bucket_file_id) > 100:
        return "Error: Invalid bucket file ID"
    
    # Get current user context from environment
    context = get_user_context()
    user_id = context.get("userId")
    user_email = context.get("userEmail")
    
    if not user_id or not user_email:
        return "Error: User not authenticated"
    
    if not VECTOR_COLLECTION_ID:
        return "Error: Vector Collection ID not configured. Please set NEXT_PUBLIC_APPWRITE_VECTOR_COLLECTION in .env"

    try:
        loop = asyncio.get_event_loop()
        # Verify user owns or has access to this file
        FILES_COLLECTION_ID = os.getenv("NEXT_PUBLIC_APPWRITE_FILES_COLLECTION")
        file_doc = await loop.run_in_executor(
            None,
            lambda: databases.get_document(
                database_id=DATABASE_ID,
                collection_id=FILES_COLLECTION_ID,
                document_id=file_id
            )
        )
        
        # Check ownership or shared access
        is_owner = file_doc.get('owner') == user_id
        is_shared = user_email in file_doc.get('users', [])
        
        if not is_owner and not is_shared:
            return "Error: You don't have access to this file"
        
        # DUPLICATE DETECTION: Check if file already indexed
        existing_vectors = await loop.run_in_executor(
            None,
            lambda: databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=VECTOR_COLLECTION_ID,
                queries=[
                    Query.equal("file_id", [file_id]),
                    Query.limit(1)
                ]
            )
        )
        
        if existing_vectors['total'] > 0:
            logger.info(f"File {file_id} already indexed with {existing_vectors['total']} vectors")
            return f"File already indexed with {existing_vectors['total']} chunks. Use 'ask' to query it."
        
        # Extract metadata
        file_name = file_doc.get('name', 'unknown')
        file_type = file_doc.get('type', 'other')
        file_size = file_doc.get('size', 0)
        created_at = file_doc.get('$createdAt', datetime.now().isoformat())
        
        # 1. Download & Extract
        result = await loop.run_in_executor(
            None,
            lambda: storage.get_file_download(BUCKET_ID, bucket_file_id)
        )
        text = smart_extract_text(result)
        logger.info(f"Extracted text length: {len(text)}")
        logger.debug(f"Text preview: {text[:200]}")
        
        if not text or not text.strip():
            return "Could not extract text from file. The document might be empty or unreadable."

        # 2. Chunking with proper text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_text(text)
        
        # 3. Embed & Store with metadata (limit to prevent overload)
        chunks_to_process = chunks[:MAX_CHUNKS_TO_INDEX]
        count = 0
        for idx, chunk in enumerate(chunks_to_process):
            vector = embeddings.embed_query(chunk)
            
            await loop.run_in_executor(
                None,
                lambda c=chunk, v=vector, i=idx: databases.create_document(
                    database_id=DATABASE_ID,
                    collection_id=VECTOR_COLLECTION_ID,
                    document_id=ID.unique(),
                    data={
                        "file_id": file_id,
                        "content": c,
                        "embedding": json.dumps(v),
                        # Metadata for filtering
                        "file_name": file_name,
                        "file_type": file_type,
                        "file_size": file_size,
                        "chunk_index": i,
                        "indexed_at": datetime.now().isoformat(),
                        "created_at": created_at,
                        "user_id": user_id
                    }
                )
            )
            count += 1
        
        logger.info(f"Indexed {count}/{len(chunks)} chunks for file {file_id}")
        return f"File processed. {count} chunks indexed ({len(chunks) - count} chunks skipped due to limit)."

    except Exception as e:
        return f"Error processing file: {str(e)}"

@tool
@handle_tool_error
@cached(vector_cache, ttl=1800, key_prefix="vector_search")
async def ask_file_question(question: str) -> str:
    """
    Search your indexed files to answer a question.
    Use this when the user asks a question about the CONTENT of their files.
    """
    # Validate input
    if not question or len(question) > 1000:
        return "Error: Invalid question (must be 1-1000 characters)"
    
    # Get current user context from environment
    context = get_user_context()
    user_id = context.get("userId")
    user_email = context.get("userEmail")
    
    if not user_id or not user_email:
        return "Error: User not authenticated"
    
    if not VECTOR_COLLECTION_ID:
        return "Error: Vector Collection ID not configured. Please set NEXT_PUBLIC_APPWRITE_VECTOR_COLLECTION in .env"
    
    try:
        loop = asyncio.get_event_loop()
        # Import for file filtering
        FILES_COLLECTION_ID = os.getenv("NEXT_PUBLIC_APPWRITE_FILES_COLLECTION")
        
        # 1. First, get user's file IDs
        user_files_result = await loop.run_in_executor(
            None,
            lambda: databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=FILES_COLLECTION_ID,
                queries=[
                    Query.or_queries([
                        Query.equal("owner", [user_id]),
                        Query.contains("users", [user_email])
                    ]),
                    Query.limit(MAX_USER_FILES)
                ]
            )
        )
        
        # Extract file IDs
        user_file_ids = [doc['$id'] for doc in user_files_result['documents']]
        
        if not user_file_ids:
            return "You have no files to search. Please upload files first."
        
        logger.info(f"User has {len(user_file_ids)} files for vector search")
        
        # 2. Embed Query for semantic search
        query_vector = embeddings.embed_query(question)
        q_vec = np.array(query_vector)
        q_norm = np.linalg.norm(q_vec)
        
        # 3. Optimized vector retrieval with batching and hybrid search
        BATCH_SIZE = 50
        all_chunks = []  # Store (content, metadata) for hybrid search
        semantic_scores = []
        
        for i in range(0, len(user_file_ids), BATCH_SIZE):
            batch_file_ids = user_file_ids[i:i+BATCH_SIZE]
            
            # Fetch vectors for this batch of files
            try:
                vectors_result = await loop.run_in_executor(
                    None,
                    lambda: databases.list_documents(
                        database_id=DATABASE_ID,
                        collection_id=VECTOR_COLLECTION_ID,
                        queries=[
                            Query.equal("file_id", batch_file_ids),
                            Query.limit(500)
                        ]
                    )
                )
            except:
                # Fallback: fetch and filter client-side for this batch
                vectors_result = await loop.run_in_executor(
                    None,
                    lambda: databases.list_documents(
                        database_id=DATABASE_ID,
                        collection_id=VECTOR_COLLECTION_ID,
                        queries=[Query.limit(500)]
                    )
                )
                batch_file_set = set(batch_file_ids)
                filtered_docs = [
                    d for d in vectors_result['documents']
                    if d.get('file_id') in batch_file_set
                ]
                vectors_result['documents'] = filtered_docs
            
            # Calculate semantic similarities for this batch
            for d in vectors_result['documents']:
                try:
                    vec = json.loads(d['embedding'])
                    d_vec = np.array(vec)
                    d_norm = np.linalg.norm(d_vec)
                    
                    # Cosine similarity
                    score = np.dot(q_vec, d_vec) / (q_norm * d_norm)
                    semantic_scores.append(score)
                    
                    # Store content and metadata
                    all_chunks.append({
                        'content': d['content'],
                        'file_name': d.get('file_name', 'unknown'),
                        'file_type': d.get('file_type', 'other'),
                        'file_id': d.get('file_id'),
                        'indexed_at': d.get('indexed_at', '')
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse vector embedding: {e}")
                    continue
        
        if not all_chunks:
            return "No indexed documents found. Please ask to 'analyze' a file first."
        
        logger.info(f"Found {len(all_chunks)} vector chunks for hybrid search")

        # 4. HYBRID SEARCH: Combine semantic + keyword (BM25)
        # Extract just the text content for BM25
        chunk_texts = [chunk['content'] for chunk in all_chunks]
        
        # Compute BM25 keyword scores
        bm25 = BM25(chunk_texts)
        keyword_scores = bm25.get_scores(question)
        
        # Normalize both score sets to [0, 1]
        norm_semantic = normalize_scores(semantic_scores)
        norm_keyword = normalize_scores(keyword_scores)
        
        # Compute hybrid scores
        final_scores = [
            (hybrid_score(sem, key), chunk)
            for sem, key, chunk in zip(norm_semantic, norm_keyword, all_chunks)
        ]
        
        # 5. RE-RANKING: Sort by hybrid score
        final_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Get top chunks with metadata
        top_results = final_scores[:TOP_CHUNKS_RETURNED]
        
        logger.info(f"Returning top {len(top_results)} chunks after hybrid search")
        
        # Format results with metadata
        formatted_results = []
        for score, chunk in top_results:
            formatted_results.append(
                f"[{chunk['file_name']}] (Score: {score:.3f})\n{chunk['content']}"
            )
        
        return "Context found:\n" + "\n---\n".join(formatted_results)

    except Exception as e:
        return f"Error searching: {str(e)}"

async def cleanup_file_vectors(file_id: str) -> Dict[str, Any]:
    """
    Clean up all vector embeddings associated with a deleted file.
    Should be called when a file is deleted to prevent orphaned vectors.
    
    Args:
        file_id: The ID of the file to clean up vectors for
        
    Returns:
        Dictionary with cleanup statistics
    """
    if not VECTOR_COLLECTION_ID:
        logger.warning("Vector collection not configured, skipping cleanup")
        return {"deleted": 0, "error": "Vector collection not configured"}
    
    try:
        loop = asyncio.get_event_loop()
        
        # Find all vectors for this file
        vectors_result = await loop.run_in_executor(
            None,
            lambda: databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=VECTOR_COLLECTION_ID,
                queries=[
                    Query.equal("file_id", [file_id]),
                    Query.limit(1000)  # Should cover most files
                ]
            )
        )
        
        deleted_count = 0
        for doc in vectors_result['documents']:
            try:
                await loop.run_in_executor(
                    None,
                    lambda d=doc: databases.delete_document(
                        database_id=DATABASE_ID,
                        collection_id=VECTOR_COLLECTION_ID,
                        document_id=d['$id']
                    )
                )
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete vector {doc['$id']}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} vectors for file {file_id}")
        return {"deleted": deleted_count, "file_id": file_id}
        
    except Exception as e:
        logger.error(f"Error cleaning up vectors for file {file_id}: {e}")
        return {"deleted": 0, "error": str(e)}

@tool
async def cleanup_orphaned_vectors() -> str:
    """
    Scan for and remove orphaned vectors (vectors whose files no longer exist).
    Use this for maintenance to clean up the vector database.
    """
    # Get current user context
    context = get_user_context()
    user_id = context.get("userId")
    
    if not user_id:
        return "Error: User not authenticated"
    
    if not VECTOR_COLLECTION_ID:
        return "Error: Vector Collection ID not configured"
    
    try:
        loop = asyncio.get_event_loop()
        FILES_COLLECTION_ID = os.getenv("NEXT_PUBLIC_APPWRITE_FILES_COLLECTION")
        
        # Get all user's file IDs
        user_files_result = await loop.run_in_executor(
            None,
            lambda: databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=FILES_COLLECTION_ID,
                queries=[
                    Query.equal("owner", [user_id]),
                    Query.limit(1000)
                ]
            )
        )
        
        valid_file_ids = set(doc['$id'] for doc in user_files_result['documents'])
        logger.info(f"User has {len(valid_file_ids)} valid files")
        
        # Get all vectors for user
        all_vectors = await loop.run_in_executor(
            None,
            lambda: databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=VECTOR_COLLECTION_ID,
                queries=[
                    Query.equal("user_id", [user_id]),
                    Query.limit(5000)
                ]
            )
        )
        
        # Find orphaned vectors
        orphaned = []
        for doc in all_vectors['documents']:
            file_id = doc.get('file_id')
            if file_id not in valid_file_ids:
                orphaned.append(doc['$id'])
        
        if not orphaned:
            return "No orphaned vectors found. Vector database is clean."
        
        # Delete orphaned vectors
        deleted_count = 0
        for vector_id in orphaned:
            try:
                await loop.run_in_executor(
                    None,
                    lambda v=vector_id: databases.delete_document(
                        database_id=DATABASE_ID,
                        collection_id=VECTOR_COLLECTION_ID,
                        document_id=v
                    )
                )
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete orphaned vector {vector_id}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} orphaned vectors")
        return f"Cleanup complete: Removed {deleted_count} orphaned vectors from {len(orphaned)} found."
        
    except Exception as e:
        return f"Error during cleanup: {str(e)}"
