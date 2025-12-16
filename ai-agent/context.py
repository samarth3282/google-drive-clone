"""
Shared user context for the AI agent.
This module provides a thread-safe way to pass user information across tools.
"""
from contextvars import ContextVar

# Thread-safe storage for user context
user_context: ContextVar[dict] = ContextVar('user_context', default={})
