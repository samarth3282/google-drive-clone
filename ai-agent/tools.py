import os
from typing import List, Optional, Dict, Any
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.query import Query
from dotenv import load_dotenv
from langchain_core.tools import tool
import warnings
import re
import os
import asyncio
import functools
warnings.filterwarnings("ignore", category=DeprecationWarning) 

from error_handling import (
    handle_tool_error,
    safe_appwrite_call,
    ValidationError,
    logger
)
from cache import file_content_cache, search_results_cache, cached, invalidate_user_cache 

load_dotenv(dotenv_path="../.env.local")

# Async wrapper for synchronous Appwrite calls
def run_async(func):
    """Wrapper to run synchronous Appwrite calls without blocking."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper

# Constants
MAX_FILENAME_LENGTH = 255
MAX_SEARCH_TEXT_LENGTH = 500
MAX_QUERY_LIMIT = 1000
DEFAULT_QUERY_LIMIT = 100
MAX_FILE_ID_LENGTH = 100
MAX_EMAILS_PER_SHARE = 50
MAX_FILE_CONTENT_LENGTH = 10000  # Increased from 5000 for better context
MAX_STORAGE_QUERY_LIMIT = 5000

# Helper function to get user context from environment
def get_user_context() -> Dict[str, str]:
    """Extract user context from environment variables set by agent."""
    return {
        "userId": os.environ.get("_CURRENT_USER_ID", ""),
        "userEmail": os.environ.get("_CURRENT_USER_EMAIL", "")
    }

# Input sanitization functions
def sanitize_filename(filename: str) -> str:
    """Remove potentially dangerous characters from filenames."""
    if not filename:
        return ""
    # Remove any characters that aren't alphanumeric, dash, underscore, dot, or space
    sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
    # Limit length
    return sanitized[:MAX_FILENAME_LENGTH].strip()

def sanitize_search_text(text: str) -> str:
    """Sanitize search text to prevent injection attacks."""
    if not text:
        return ""
    # Remove special characters that could be used for injection
    # Allow alphanumeric, spaces, and basic punctuation
    sanitized = re.sub(r'[<>{}\\$;]', '', text)
    return sanitized[:MAX_SEARCH_TEXT_LENGTH].strip()

def validate_email(email: str) -> bool:
    """Basic email validation."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

# Initialize Appwrite Client
client = Client()
client.set_endpoint(os.getenv("NEXT_PUBLIC_APPWRITE_ENDPOINT"))
client.set_project(os.getenv("NEXT_PUBLIC_APPWRITE_PROJECT"))
client.set_key(os.getenv("NEXT_APPWRITE_KEY"))

databases = Databases(client)
storage = Storage(client)

DATABASE_ID = os.getenv("NEXT_PUBLIC_APPWRITE_DATABASE")
FILES_COLLECTION_ID = os.getenv("NEXT_PUBLIC_APPWRITE_FILES_COLLECTION")
BUCKET_ID = os.getenv("NEXT_PUBLIC_APPWRITE_BUCKET")

@tool
@handle_tool_error
@cached(search_results_cache, ttl=300, key_prefix="search")
async def search_files(search_text: Optional[str] = None, types: Optional[List[str]] = None, limit: Optional[int] = None) -> str:
    """
    Search for files by name or type.
    Use this when the user asks specifically to find files (e.g. "Find my invoices").
    output format: "Name: ..., ID: ..., BucketFileID: ..., Type: ..., Size: ..."
    """
    # Get current user context from environment
    context = get_user_context()
    user_id = context.get("userId")
    user_email = context.get("userEmail")
    
    logger.info(f"search_files called by user: {user_id}")
    
    if not user_id or not user_email:
        raise ValidationError("User not authenticated")
    
    # Sanitize inputs
    if search_text:
        search_text = sanitize_search_text(search_text)
        if not search_text:
            raise ValidationError("Invalid search text")
    
    # Validate types
    valid_types = ["document", "image", "video", "audio", "other"]
    if types:
        types = [t for t in types if t in valid_types]
    
    # Limit validation
    if limit:
        limit = max(1, min(limit, MAX_QUERY_LIMIT))  # Clamp between 1 and MAX_QUERY_LIMIT
    
    queries = []
    
    # CRITICAL: Filter by owner OR shared with user
    # This matches the logic in file.actions.ts
    queries.append(Query.or_queries([
        Query.equal("owner", [user_id]),
        Query.contains("users", [user_email])
    ]))
    
    if search_text:
        queries.append(Query.contains("name", search_text))
    if types:
        queries.append(Query.equal("type", types))
    if limit:
        queries.append(Query.limit(limit))

    # Run in executor to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: safe_appwrite_call(
            databases.list_documents,
            database_id=DATABASE_ID,
            collection_id=FILES_COLLECTION_ID,
            queries=queries
        )
    )
    
    # Parse result to be more friendly for LLM
    files = []
    for doc in result['documents']:
        # Safe access to bucketFileId (might be missing in old docs)
        bucket_file_id = doc.get("bucketFileId", "N/A")
        files.append(f"Name: {doc['name']}, ID: {doc['$id']}, BucketFileID: {bucket_file_id}, Type: {doc['type']}, Size: {doc['size']}")
    
    return "\n".join(files) if files else "No files found."

@tool
async def rename_file(file_id: str, new_name: str) -> str:
    """
    Rename a file.
    Args:
        file_id: The ID of the file document.
        new_name: The new name (WITHOUT extension).
    """
    # Sanitize inputs
    new_name = sanitize_filename(new_name)
    if not new_name:
        return "Error: Invalid file name"
    
    if not file_id or len(file_id) > MAX_FILE_ID_LENGTH:
        return "Error: Invalid file ID"
    
    try:
        # 1. Get existing document to find current extension
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(
            None,
            lambda: databases.get_document(
                database_id=DATABASE_ID,
                collection_id=FILES_COLLECTION_ID,
                document_id=file_id
            )
        )
        original_name = doc['name']
        extension = ""
        if "." in original_name:
            extension = original_name.split(".")[-1]
        
        # 2. Construct new name
        # Check if user provided extension in new_name
        full_name = new_name
        if extension and not new_name.endswith(f".{extension}"):
            full_name = f"{new_name}.{extension}"

        # 3. Update
        await loop.run_in_executor(
            None,
            lambda: databases.update_document(
                database_id=DATABASE_ID,
                collection_id=FILES_COLLECTION_ID,
                document_id=file_id,
                data={"name": full_name}
            )
        )
        
        # Invalidate caches since file list changed
        context = get_user_context()
        if context.get("userId"):
            invalidate_user_cache(context["userId"])
        
        return f"File {file_id} successfully renamed to {full_name}."
    except Exception as e:
        return f"Error renaming file: {str(e)}"

@tool
async def delete_file(file_id: str, bucket_file_id: str) -> str:
    """
    Delete a file.
    Args:
        file_id: The ID of the file DOCUMENT in the database.
        bucket_file_id: The ID of the actual file in STORAGE (bucket).
    """
    # Validate inputs
    if not file_id or len(file_id) > MAX_FILE_ID_LENGTH:
        return "Error: Invalid file ID"
    if not bucket_file_id or len(bucket_file_id) > MAX_FILE_ID_LENGTH:
        return "Error: Invalid bucket file ID"
    
    try:
        loop = asyncio.get_event_loop()
        # 1. Delete Document
        await loop.run_in_executor(
            None,
            lambda: databases.delete_document(
                database_id=DATABASE_ID,
                collection_id=FILES_COLLECTION_ID,
                document_id=file_id
            )
        )
        # 2. Delete from Storage
        await loop.run_in_executor(
            None,
            lambda: storage.delete_file(
                bucket_id=BUCKET_ID,
                file_id=bucket_file_id
            )
        )
        
        # 3. Clean up associated vector embeddings
        from rag import cleanup_file_vectors
        cleanup_result = await cleanup_file_vectors(file_id)
        logger.info(f"Vector cleanup for file {file_id}: {cleanup_result}")
        
        # Invalidate caches since file was deleted
        context = get_user_context()
        if context.get("userId"):
            invalidate_user_cache(context["userId"])
        
        vectors_deleted = cleanup_result.get('deleted', 0)
        return f"File {file_id} successfully deleted. Cleaned up {vectors_deleted} vector embeddings."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@tool
async def share_file(file_id: str, emails: List[str]) -> str:
    """
    Share a file with other users.
    Args:
        file_id: The ID of the file document.
        emails: List of email addresses to share with.
    """
    # Validate inputs
    if not file_id or len(file_id) > MAX_FILE_ID_LENGTH:
        return "Error: Invalid file ID"
    
    # Validate and sanitize emails
    valid_emails = []
    for email in emails:
        email = email.strip().lower()
        if validate_email(email):
            valid_emails.append(email)
    
    if not valid_emails:
        return "Error: No valid email addresses provided"
    
    if len(valid_emails) > MAX_EMAILS_PER_SHARE:
        return f"Error: Cannot share with more than {MAX_EMAILS_PER_SHARE} users at once"
    
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: databases.update_document(
                database_id=DATABASE_ID,
                collection_id=FILES_COLLECTION_ID,
                document_id=file_id,
                data={"users": valid_emails}
            )
        )
        return f"File shared with {', '.join(valid_emails)}"
    except Exception as e:
        return f"Error sharing file: {str(e)}"

@tool
async def get_storage_stats() -> str:
    """Get total storage used."""
    # Get current user context from environment
    context = get_user_context()
    user_id = context.get("userId")
    
    if not user_id:
        return "Error: User not authenticated"
    
    try:
        loop = asyncio.get_event_loop()
        # Filter by owner only (same as getTotalSpaceUsed in file.actions.ts)
        result = await loop.run_in_executor(
            None,
            lambda: databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=FILES_COLLECTION_ID,
                queries=[
                    Query.equal("owner", [user_id]),
                    Query.limit(MAX_STORAGE_QUERY_LIMIT)
                ]
            )
        )
        total_size = sum([d['size'] for d in result['documents']])
        return f"Total storage used: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)"
    except Exception as e:
        return f"Error getting stats: {str(e)}"

@tool
@cached(file_content_cache, ttl=600, key_prefix="file_content")
async def read_file_content(file_id: str, bucket_file_id: str) -> str:
    """
    Read and return the contents of a text file.
    Use this when the user asks about the contents of a text file (txt, md, json, xml, csv, etc).
    For PDFs or other complex documents, use process_file_for_search and ask_file_question instead.
    Args:
        file_id: The ID of the file document.
        bucket_file_id: The ID of the file in storage.
    """
    # Validate inputs
    if not file_id or len(file_id) > MAX_FILE_ID_LENGTH:
        return "Error: Invalid file ID"
    if not bucket_file_id or len(bucket_file_id) > MAX_FILE_ID_LENGTH:
        return "Error: Invalid bucket file ID"
    
    # Get current user context from environment
    context = get_user_context()
    user_id = context.get("userId")
    user_email = context.get("userEmail")
    
    if not user_id or not user_email:
        return "Error: User not authenticated"
    
    try:
        loop = asyncio.get_event_loop()
        # Verify user owns or has access to this file
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
        
        # Download file
        file_bytes = await loop.run_in_executor(
            None,
            lambda: storage.get_file_download(BUCKET_ID, bucket_file_id)
        )
        
        # Try to decode as text
        try:
            content = file_bytes.decode('utf-8')
            # Limit output to avoid token overflow
            if len(content) > MAX_FILE_CONTENT_LENGTH:
                return f"File content (first {MAX_FILE_CONTENT_LENGTH} characters):\n\n{content[:MAX_FILE_CONTENT_LENGTH]}\n\n... (truncated, file is {len(content)} characters total)"
            return f"File content:\n\n{content}"
        except UnicodeDecodeError:
            return "Error: This file is not a text file or uses an unsupported encoding. For PDF files, please use the 'analyze' function first."
            
    except Exception as e:
        return f"Error reading file: {str(e)}"
