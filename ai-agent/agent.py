import os
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from tools import search_files, rename_file, delete_file, share_file, get_storage_stats, read_file_content
from rag import process_file_for_search, ask_file_question, cleanup_orphaned_vectors
from error_handling import logger

load_dotenv(dotenv_path="../.env.local")

# Define Agent State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    userId: str  # User ID for filtering files
    userEmail: str  # User email for filtering files

# Initialize Model
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
    max_retries=5 
)

# Bind Tools
tools = [search_files, rename_file, delete_file, share_file, get_storage_stats, read_file_content, process_file_for_search, ask_file_question, cleanup_orphaned_vectors]
llm_with_tools = llm.bind_tools(tools)

# System Prompt
SYSTEM_PROMPT = """You are a helpful File Management Assistant.
Your goal is to help users manage their files in a storage system.

CRITICAL RULES:
1. BEFORE performing any action (Rename, Delete, Share, Read), you MUST FIRST search for the file to get its 'ID' and 'BucketFileID'.
2. If you don't know the ID, use the `search_files` tool with the filename.
3. When renaming, you only need to provide the 'new_name'. The system will handle the extension.
4. When deleting, you need BOTH 'file_id' and 'bucket_file_id' (found via search).
5. For reading TEXT file contents (txt, md, json, csv, xml), use the `read_file_content` tool after searching for the file.
6. For PDF files or complex document analysis, use `process_file_for_search` first, then `ask_file_question`.
7. Always confirm the action to the user after completion.
8. DO NOT show 'ID' or 'BucketFileID' in your final response to the user unless strictly necessary or asked. Keep the response clean and natural.
"""

# Define Logic
def chatbot(state: AgentState) -> Dict[str, List[BaseMessage]]:
    logger.info(f"Chatbot invoked with {len(state['messages'])} messages")
    
    messages = state["messages"]
    if not messages or messages[0].type != "system":
         # Inject system prompt at the start
         from langchain_core.messages import SystemMessage
         messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Retry logic for 429 Errors and network issues
    import time
    from google.api_core.exceptions import ResourceExhausted

    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
             result = llm_with_tools.invoke(messages)
             logger.info(f"LLM response generated successfully")
             return {"messages": [result]}
        except ResourceExhausted as e:
            if attempt < max_retries:
                wait = (attempt + 1) * 5
                logger.warning(f"Rate limit hit. Retrying in {wait}s... (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(wait)
            else:
                logger.error(f"Rate limit exceeded after {max_retries} retries")
                raise
        except ConnectionError as e:
            if attempt < max_retries:
                wait = (attempt + 1) * 3
                logger.warning(f"Connection error. Retrying in {wait}s... (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(wait)
            else:
                logger.error(f"Connection failed after {max_retries} retries")
                raise
        except Exception as e:
            logger.error(f"Unexpected error in chatbot: {str(e)}")
            raise

# Custom tool node that passes user context via environment
import os

def tools_with_context(state: AgentState) -> Dict[str, List[BaseMessage]]:
    """Execute tools with user context passed via environment variables."""
    from langgraph.prebuilt import ToolNode
    
    # Set user context in environment (thread-safe in async)
    user_id = state.get("userId", "")
    user_email = state.get("userEmail", "")
    
    # Store in os.environ for this execution
    os.environ["_CURRENT_USER_ID"] = user_id
    os.environ["_CURRENT_USER_EMAIL"] = user_email
    
    logger.info(f"Executing tools for user: {user_id}")
    
    try:
        # Execute tools
        tool_node = ToolNode(tools)
        result = tool_node.invoke(state)
        logger.info("Tools executed successfully")
        return result
    except Exception as e:
        logger.error(f"Tool execution failed: {str(e)}")
        raise
    finally:
        # Clean up
        os.environ.pop("_CURRENT_USER_ID", None)
        os.environ.pop("_CURRENT_USER_EMAIL", None)

# Build Graph
graph_builder = StateGraph(AgentState)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tools_with_context)

graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")

# Conditional Edge: If tool call -> go to tools, else -> END
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)

agent_executor = graph_builder.compile()
