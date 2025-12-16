import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import agent_executor
from langchain_core.messages import HumanMessage, AIMessage
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Get allowed origins from environment variable
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# Allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    userId: str
    userEmail: str
    history: list = [] # Optional: Pass history if needed, but we keep it simple

@app.get("/")
def read_root():
    return {"status": "AI Agent is running"}

@app.get("/health")
def health_check():
    """Detailed health check to verify all dependencies"""
    try:
        # Check if agent is imported
        from agent import agent_executor
        
        # Check environment variables
        env_vars = {
            "GOOGLE_API_KEY": "✓" if os.getenv("GOOGLE_API_KEY") else "✗",
            "NEXT_PUBLIC_APPWRITE_PROJECT": "✓" if os.getenv("NEXT_PUBLIC_APPWRITE_PROJECT") else "✗",
            "VECTOR_COLLECTION_ID": "✓" if os.getenv("VECTOR_COLLECTION_ID") else "✗",
            "ALLOWED_ORIGINS": os.getenv("ALLOWED_ORIGINS", "not set"),
        }
        
        return {
            "status": "healthy",
            "agent_loaded": True,
            "environment": env_vars
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

from fastapi.responses import StreamingResponse
import json

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Pass user context to the agent
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "userId": request.userId,
            "userEmail": request.userEmail,
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
