"""Flask middleware for API request logging."""

import logging
import time
from flask import Flask, request, g
from functools import wraps

logger = logging.getLogger(__name__)


def setup_request_logging(app: Flask) -> None:
    """Setup request/response logging middleware."""
    
    @app.before_request
    def before_request():
        """Log incoming request and store start time."""
        g.start_time = time.time()
        
        # Log request details
        logger.info(
            f"Incoming Request: {request.method} {request.path}",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.user_agent.string if request.user_agent else "Unknown"
            }
        )
    
    @app.after_request
    def after_request(response):
        """Log response and calculate request duration."""
        try:
            # Calculate request duration
            duration = time.time() - g.start_time if hasattr(g, 'start_time') else 0
            
            # Determine log level based on status code
            if response.status_code >= 500:
                log_level = logger.error
            elif response.status_code >= 400:
                log_level = logger.warning
            else:
                log_level = logger.info
            
            # Log response
            log_level(
                f"Response: {response.status_code} {request.method} {request.path} ({duration:.3f}s)"
            )
        except Exception as e:
            logger.error(f"Error logging response: {str(e)}")
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Log unhandled exceptions."""
        logger.error(
            f"Unhandled Exception: {str(error)}",
            extra={"error_type": type(error).__name__},
            exc_info=True
        )
        
        # Return generic error response
        return {
            "error": "Internal Server Error",
            "status": 500
        }, 500


def log_api_call(function):
    """Decorator to log specific API function calls."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {function.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = function(*args, **kwargs)
            logger.debug(f"Function {function.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(
                f"Error in {function.__name__}: {str(e)}",
                extra={"function": function.__name__, "error_type": type(e).__name__},
                exc_info=True
            )
            raise
    return wrapper
