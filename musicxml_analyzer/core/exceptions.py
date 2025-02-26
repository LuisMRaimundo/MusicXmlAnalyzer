# core/exceptions.py

"""
Custom exceptions and error handling for MusicXML analysis.
"""

import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union

logger = logging.getLogger(__name__)

class MusicXMLAnalysisError(Exception):
    """Base class for all MusicXML analysis exceptions."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)
        
    def __str__(self) -> str:
        if self.original_exception:
            return f"{self.message} (Caused by: {type(self.original_exception).__name__}: {self.original_exception})"
        return self.message


class ScoreParsingError(MusicXMLAnalysisError):
    """Raised when there is an error parsing the MusicXML score."""
    pass


class AnalysisError(MusicXMLAnalysisError):
    """Raised when there is an error during analysis."""
    pass


class VisualizationError(MusicXMLAnalysisError):
    """Raised when there is an error during visualization."""
    pass


class ValidationError(MusicXMLAnalysisError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(MusicXMLAnalysisError):
    """Raised when there is an issue with configuration."""
    pass


def handle_exceptions(error_type: Type[MusicXMLAnalysisError], error_message: str = None):
    """
    Decorator for handling exceptions in MusicXML analysis functions.
    
    Args:
        error_type: The type of MusicXMLAnalysisError to raise
        error_message: Optional custom error message
        
    Example:
        @handle_exceptions(AnalysisError, "Error analyzing dynamics")
        def analyze_dynamics(score_data):
            # Analysis implementation...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except MusicXMLAnalysisError:
                # Re-raise existing MusicXMLAnalysisErrors without wrapping
                raise
            except Exception as e:
                # Get function name and arguments for detailed error message
                func_name = func.__name__
                args_str = ", ".join([str(a) for a in args])
                kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
                
                # Create detailed error message
                message = error_message or f"Error in {func_name}({args_str}{', ' if args_str and kwargs_str else ''}{kwargs_str})"
                
                # Log the error with stack trace
                logger.error(f"{message}: {e}")
                logger.debug(f"Stack trace: {traceback.format_exc()}")
                
                # Raise custom exception
                raise error_type(message, e)
        return wrapper
    return decorator


def validate_score(score_data):
    """
    Validates that score data is properly formatted.
    Raises ValidationError if validation fails.
    """
    if not score_data:
        raise ValidationError("Score data is empty")
    
    if not hasattr(score_data, 'notes') or not score_data.notes:
        raise ValidationError("Score contains no notes")
    
    return True


def validate_input(validation_func: Callable, error_message: str = None):
    """
    Decorator for validating input parameters.
    
    Args:
        validation_func: Function that validates inputs and returns True/False
        error_message: Optional custom error message
        
    Example:
        def validate_density_params(interval):
            return interval > 0
            
        @validate_input(validate_density_params, "Invalid density interval")
        def analyze_density(score_data, interval=10.0):
            # Implementation...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not validation_func(*args, **kwargs):
                message = error_message or f"Validation failed for {func.__name__}"
                logger.error(message)
                raise ValidationError(message)
            return func(*args, **kwargs)
        return wrapper
    return decorator