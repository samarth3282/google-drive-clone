from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr, field_validator
from agent import agent_executor
from langchain_core.messages import HumanMessage, AIMessage
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List, Any
import os
from appwrite.client import Client
from appwrite.services.account import Account

app = FastAPI()

# Constants
MAX_MESSAGE_LENGTH = 10000
MAX_HISTORY_LENGTH = 20

# Allow origins from environment variable (comma-separated)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def verify_session_token(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    """
    Verify the session token and return the authenticated user.
    Token should be sent as: Authorization: Bearer <session_token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header. Use: Authorization: Bearer <token>"
        )
    
    session_token = authorization.replace("Bearer ", "").strip()
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Session token is required")
    
    try:
        # Initialize Appwrite client with session token
        client = Client()
        client.set_endpoint(os.getenv("NEXT_PUBLIC_APPWRITE_ENDPOINT"))
        client.set_project(os.getenv("NEXT_PUBLIC_APPWRITE_PROJECT"))
        client.set_session(session_token)
        
        # Verify session by getting account info
        account = Account(client)
        user = account.get()
        
        return {
            "userId": user["$id"],
            "email": user["email"],
            "name": user.get("name", "")
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired session token: {str(e)}"
        )

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []  # List of previous messages [{"role": "user/ai", "content": "..."}]
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(f'Message too long (max {MAX_MESSAGE_LENGTH} characters)')
        return v.strip()
    
    @field_validator('history')
    @classmethod
    def validate_history(cls, v: List[Dict[str, str]]) -> List[Dict[str, str]]:
        # Limit history to last MAX_HISTORY_LENGTH messages to avoid token overflow
        if len(v) > MAX_HISTORY_LENGTH:
            return v[-MAX_HISTORY_LENGTH:]
        return v

@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "AI Agent is running"}

from fastapi.responses import StreamingResponse
import json

@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    user: Dict[str, str] = Depends(verify_session_token)
):
    """
    Chat endpoint with authentication and conversation history.
    Requires Authorization header with session token.
    """
    try:
        # Convert history to LangChain messages
        from langchain_core.messages import HumanMessage, AIMessage
        
        history_messages = []
        for msg in request.history:
            if msg.get("role") == "user":
                history_messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "ai":
                history_messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        history_messages.append(HumanMessage(content=request.message))
        
        # Use authenticated user's info (not from request body)
        initial_state = {
            "messages": history_messages,
            "userId": user["userId"],
            "userEmail": user["email"],
        }
        
        async def event_stream():
            # Use astream_events to catch token generation
            async for event in agent_executor.astream_events(initial_state, version="v1"):
                kind = event["event"]
                
                # Check for LLM streaming events from the 'chatbot' node (or relevant model call)
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        # Handle structured content (list) in stream
                        if isinstance(content, list):
                            text_parts = []
                            for part in content:
                                if isinstance(part, dict) and "text" in part:
                                    text_parts.append(part["text"])
                                elif isinstance(part, str):
                                    text_parts.append(part)
                            content = "".join(text_parts)
                        
                        # Ensure content is string before yielding
                        if isinstance(content, str):
                             yield content

        return StreamingResponse(event_stream(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
