import os
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from tools import search_files, rename_file, delete_file, share_file, get_storage_stats, read_file_content
from rag import process_file_for_search, ask_file_question

load_dotenv(dotenv_path="../.env.local")

# Configure LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "gdrive-clone")

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
tools = [search_files, rename_file, delete_file, share_file, get_storage_stats, read_file_content, process_file_for_search, ask_file_question]
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

FILE TYPE CATEGORIES:
- When users ask for "PDF files", "Word documents", "Excel files", etc., these are all stored as type="document"
- To find PDF files specifically: use search_files with types=["document"] AND search_text=".pdf"
- To find Word docs: use types=["document"] AND search_text=".doc"
- To find Excel files: use types=["document"] AND search_text=".xls"
- To find images: use types=["image"]
- To find videos: use types=["video"]
- To find audio: use types=["audio"]
"""

# Define Logic
def chatbot(state: AgentState):
    print("--- Invoking Model ---")
    print(f"Messages: {len(state['messages'])}")
    for m in state["messages"]:
        print(f"- {m.type}: {m.content} (Tools: {getattr(m, 'tool_calls', 'None')})")
    
    messages = state["messages"]
    if not messages or messages[0].type != "system":
         # Inject system prompt at the start
         from langchain_core.messages import SystemMessage
         messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    # Retry logic for 429 Errors
    import time
    from google.api_core.exceptions import ResourceExhausted

    max_retries = 3
    for attempt in range(max_retries):
        try:
             return {"messages": [llm_with_tools.invoke(messages)]}
        except Exception as e:
            if "429" in str(e) or isinstance(e, ResourceExhausted):
                wait = (attempt + 1) * 5
                print(f"WARNING: Rate limit hit. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise e
    
    # Final attempt
    return {"messages": [llm_with_tools.invoke(messages)]}

# Custom tool node that injects user context
from context import user_context

def tools_with_context(state: AgentState):
    """Execute tools with user context injected."""
    from langgraph.prebuilt import ToolNode
    
    # Store user context for tools to access
    context = {
        "userId": state.get("userId"),
        "userEmail": state.get("userEmail"),
    }
    user_context.set(context)
    
    print(f"DEBUG: Setting user context: {context}")
    
    # Execute tools
    tool_node = ToolNode(tools)
    return tool_node.invoke(state)

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
