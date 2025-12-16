"""
Error handling utilities for the AI agent.
Provides consistent error recovery across all tools and operations.
"""
import logging
from typing import Callable, Any
from functools import wraps
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentError(Exception):
    """Base exception for agent errors."""
    pass

class AuthenticationError(AgentError):
    """User authentication failed."""
    pass

class AppwriteError(AgentError):
    """Appwrite service error."""
    pass

class NetworkError(AgentError):
    """Network connectivity error."""
    pass

class ValidationError(AgentError):
    """Input validation error."""
    pass

def with_retry(max_retries: int = 3, backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator to retry function on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for wait time between retries
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {str(e)}")
                        break
                    
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}). Retrying in {wait_time}s... Error: {str(e)}")
                    time.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator

def handle_tool_error(func: Callable) -> Callable:
    """
    Decorator to handle tool errors gracefully and return user-friendly messages.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> str:
        try:
            return func(*args, **kwargs)
        except AuthenticationError as e:
            logger.error(f"Authentication error in {func.__name__}: {str(e)}")
            return f"Authentication Error: {str(e)}. Please log in again."
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
            return f"Invalid Input: {str(e)}"
        except AppwriteError as e:
            logger.error(f"Appwrite error in {func.__name__}: {str(e)}")
            return f"Database Error: Unable to complete the operation. Please try again later."
        except NetworkError as e:
            logger.error(f"Network error in {func.__name__}: {str(e)}")
            return f"Network Error: Unable to connect to the service. Please check your connection."
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return f"Unexpected Error: {str(e)}. Please contact support if this persists."
    
    return wrapper

def safe_appwrite_call(func: Callable, *args, **kwargs) -> Any:
    """
    Safely execute an Appwrite API call with retry logic and error handling.
    """
    from appwrite.exception import AppwriteException
    
    @with_retry(max_retries=3, exceptions=(AppwriteException, ConnectionError, TimeoutError))
    def execute():
        try:
            return func(*args, **kwargs)
        except AppwriteException as e:
            if e.code == 401 or e.code == 403:
                raise AuthenticationError(f"Appwrite authentication failed: {e.message}")
            elif e.code == 404:
                raise ValidationError(f"Resource not found: {e.message}")
            elif e.code >= 500:
                raise AppwriteError(f"Appwrite service error: {e.message}")
            else:
                raise AppwriteError(f"Appwrite error {e.code}: {e.message}")
        except (ConnectionError, TimeoutError) as e:
            raise NetworkError(f"Network error: {str(e)}")
    
    return execute()
