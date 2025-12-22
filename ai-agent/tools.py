import os
from typing import List, Optional
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.query import Query
from dotenv import load_dotenv
from langchain_core.tools import tool
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

load_dotenv(dotenv_path="../.env.local")

# Import shared user context
from context import user_context

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
def search_files(search_text: str = None, types: List[str] = None, limit: int = None):
    """
    Search for files by name or type.
    Use this when the user asks specifically to find files (e.g. "Find my invoices" or "Find my PDFs").
    
    IMPORTANT: File types in the database are:
    - "document" (includes: pdf, doc, docx, txt, xls, xlsx, csv, etc.)
    - "image" (includes: jpg, jpeg, png, gif, bmp, svg, webp)
    - "video" (includes: mp4, avi, mov, mkv, webm)
    - "audio" (includes: mp3, wav, ogg, flac)
    - "other" (any other file type)
    
    To find PDF files specifically, use types=["document"] AND search_text=".pdf"
    To find images, use types=["image"]
    To find specific file extensions, include the extension in search_text (e.g. ".xlsx" or ".docx")
    
    output format: "Name: ..., ID: ..., BucketFileID: ..., Type: ..., Size: ..."
    """
    # Get current user context
    context = user_context.get()
    user_id = context.get("userId")
    user_email = context.get("userEmail")
    
    print(f"DEBUG: search_files - Retrieved context: {context}")
    print(f"DEBUG: search_files - userId: {user_id}, userEmail: {user_email}")
    
    if not user_id or not user_email:
        return "Error: User not authenticated"
    
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

    try:
        result = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=FILES_COLLECTION_ID,
            queries=queries
        )
        # Parse result to be more friendly for LLM
        files = []
        for doc in result['documents']:
            # Safe access to bucketFileId (might be missing in old docs)
            bucket_file_id = doc.get("bucketFileId", "N/A")
            files.append(f"Name: {doc['name']}, ID: {doc['$id']}, BucketFileID: {bucket_file_id}, Type: {doc['type']}, Size: {doc['size']}")
        return "\n".join(files) if files else "No files found."
    except Exception as e:
        return f"Error searching files: {str(e)}"

@tool
def rename_file(file_id: str, new_name: str):
    """
    Rename a file.
    Args:
        file_id: The ID of the file document.
        new_name: The new name (WITHOUT extension).
    """
    try:
        # 1. Get existing document to find current extension
        doc = databases.get_document(
            database_id=DATABASE_ID,
            collection_id=FILES_COLLECTION_ID,
            document_id=file_id
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
        databases.update_document(
            database_id=DATABASE_ID,
            collection_id=FILES_COLLECTION_ID,
            document_id=file_id,
            data={"name": full_name}
        )
        return f"File {file_id} successfully renamed to {full_name}."
    except Exception as e:
        return f"Error renaming file: {str(e)}"

@tool
def delete_file(file_id: str, bucket_file_id: str):
    """
    Delete a file.
    Args:
        file_id: The ID of the file DOCUMENT in the database.
        bucket_file_id: The ID of the actual file in STORAGE (bucket).
    """
    try:
        # 1. Delete Document
        databases.delete_document(
            database_id=DATABASE_ID,
            collection_id=FILES_COLLECTION_ID,
            document_id=file_id
        )
        # 2. Delete from Storage
        storage.delete_file(
            bucket_id=BUCKET_ID,
            file_id=bucket_file_id
        )
        return f"File {file_id} successfully deleted."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@tool
def share_file(file_id: str, emails: List[str]):
    """
    Share a file with other users.
    Args:
        file_id: The ID of the file document.
        emails: List of email addresses to share with.
    """
    try:
        databases.update_document(
            database_id=DATABASE_ID,
            collection_id=FILES_COLLECTION_ID,
            document_id=file_id,
            data={"users": emails}
        )
        return f"File shared with {', '.join(emails)}"
    except Exception as e:
        return f"Error sharing file: {str(e)}"

@tool
def get_storage_stats():
    """Get total storage used."""
    # Get current user context
    context = user_context.get()
    user_id = context.get("userId")
    
    if not user_id:
        return "Error: User not authenticated"
    
    try:
        # Filter by owner only (same as getTotalSpaceUsed in file.actions.ts)
        result = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=FILES_COLLECTION_ID,
            queries=[
                Query.equal("owner", [user_id]),
                Query.limit(5000)
            ]
        )
        total_size = sum([d['size'] for d in result['documents']])
        return f"Total storage used: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)"
    except Exception as e:
        return f"Error getting stats: {str(e)}"

@tool
def read_file_content(file_id: str, bucket_file_id: str):
    """
    Read and return the contents of a text file.
    Use this when the user asks about the contents of a text file (txt, md, json, xml, csv, etc).
    For PDFs or other complex documents, use process_file_for_search and ask_file_question instead.
    Args:
        file_id: The ID of the file document.
        bucket_file_id: The ID of the file in storage.
    """
    # Get current user context
    context = user_context.get()
    user_id = context.get("userId")
    user_email = context.get("userEmail")
    
    if not user_id or not user_email:
        return "Error: User not authenticated"
    
    try:
        # Verify user owns or has access to this file
        file_doc = databases.get_document(
            database_id=DATABASE_ID,
            collection_id=FILES_COLLECTION_ID,
            document_id=file_id
        )
        
        # Check ownership or shared access
        is_owner = file_doc.get('owner') == user_id
        is_shared = user_email in file_doc.get('users', [])
        
        if not is_owner and not is_shared:
            return "Error: You don't have access to this file"
        
        # Download file
        file_bytes = storage.get_file_download(BUCKET_ID, bucket_file_id)
        
        # Try to decode as text
        try:
            content = file_bytes.decode('utf-8')
            # Limit output to avoid token overflow
            if len(content) > 5000:
                return f"File content (first 5000 characters):\n\n{content[:5000]}\n\n... (truncated, file is {len(content)} characters total)"
            return f"File content:\n\n{content}"
        except UnicodeDecodeError:
            return "Error: This file is not a text file or uses an unsupported encoding. For PDF files, please use the 'analyze' function first."
            
    except Exception as e:
        return f"Error reading file: {str(e)}"
