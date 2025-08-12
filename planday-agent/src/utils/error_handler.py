"""
Enhanced Error Handling and Exception Management for PlanDay Agent System

This module provides comprehensive error handling capabilities:
1. Custom exception classes for different error types
2. Error recovery strategies
3. User-friendly error messages
4. System resilience mechanisms
"""

import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
import structlog

logger = structlog.get_logger()


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"              # Minor issues, system can continue normally
    MEDIUM = "medium"        # Moderate issues, some features may be affected
    HIGH = "high"           # Serious issues, system functionality impacted
    CRITICAL = "critical"   # Critical errors, system may be unstable


class ErrorCategory(Enum):
    """Error categories for better classification"""
    SYSTEM = "system"                   # System-level errors (infrastructure, OS)
    DEPENDENCY = "dependency"           # External dependency issues (APIs, services)
    CONFIGURATION = "configuration"    # Configuration and setup issues
    USER_INPUT = "user_input"          # Invalid user input
    AUTHENTICATION = "authentication"  # Auth and permission issues
    NETWORK = "network"                # Network connectivity issues
    DATA = "data"                      # Data processing and validation issues
    INTERNAL = "internal"              # Internal application errors


class PlanDayError(Exception):
    """Base exception class for PlanDay application errors"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.INTERNAL,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 context: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
            "timestamp": self.timestamp.isoformat(),
            "traceback": traceback.format_exc() if self.cause else None
        }


class ConfigurationError(PlanDayError):
    """Configuration and setup related errors"""
    
    def __init__(self, message: str, missing_config: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.CONFIGURATION, **kwargs)
        if missing_config:
            self.context["missing_config"] = missing_config


class DependencyError(PlanDayError):
    """External dependency related errors"""
    
    def __init__(self, message: str, dependency_name: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.DEPENDENCY, **kwargs)
        if dependency_name:
            self.context["dependency_name"] = dependency_name


class MCPToolError(PlanDayError):
    """MCP tool specific errors"""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, 
                 operation: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.DEPENDENCY, **kwargs)
        if tool_name:
            self.context["tool_name"] = tool_name
        if operation:
            self.context["operation"] = operation


class LLMError(PlanDayError):
    """LLM invocation related errors"""
    
    def __init__(self, message: str, model_name: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.DEPENDENCY, **kwargs)
        if model_name:
            self.context["model_name"] = model_name


class ValidationError(PlanDayError):
    """Data validation related errors"""
    
    def __init__(self, message: str, field_name: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.DATA, **kwargs)
        if field_name:
            self.context["field_name"] = field_name


class AuthenticationError(PlanDayError):
    """Authentication and permission related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.AUTHENTICATION, 
                        ErrorSeverity.HIGH, **kwargs)


class NetworkError(PlanDayError):
    """Network connectivity related errors"""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCategory.NETWORK, **kwargs)
        if endpoint:
            self.context["endpoint"] = endpoint


class ErrorHandler:
    """
    Centralized error handling system with recovery strategies
    """
    
    def __init__(self):
        self.error_history: List[PlanDayError] = []
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {
            ErrorCategory.SYSTEM: [],
            ErrorCategory.DEPENDENCY: [],
            ErrorCategory.CONFIGURATION: [],
            ErrorCategory.USER_INPUT: [],
            ErrorCategory.AUTHENTICATION: [],
            ErrorCategory.NETWORK: [],
            ErrorCategory.DATA: [],
            ErrorCategory.INTERNAL: []
        }
        self.max_history_size = 100
        
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle an error with appropriate logging, recovery, and user messaging
        
        Returns a standardized error response for the user
        """
        # Convert to PlanDayError if not already
        if not isinstance(error, PlanDayError):
            planday_error = self._classify_error(error, context)
        else:
            planday_error = error
            
        # Add to error history
        self._record_error(planday_error)
        
        # Log the error
        self._log_error(planday_error)
        
        # Attempt recovery
        recovery_success = self._attempt_recovery(planday_error)
        
        # Generate user-friendly response
        user_response = self._generate_user_response(planday_error, recovery_success)
        
        return {
            "success": False,
            "error": {
                "category": planday_error.category.value,
                "severity": planday_error.severity.value,
                "message": planday_error.message,
                "user_message": user_response,
                "recovery_attempted": recovery_success,
                "timestamp": planday_error.timestamp.isoformat()
            }
        }
    
    def _classify_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> PlanDayError:
        """Classify a generic exception into a PlanDayError"""
        error_str = str(error).lower()
        
        # Classification logic based on error message patterns
        if "permission" in error_str or "access" in error_str or "denied" in error_str:
            return AuthenticationError(str(error), context=context, cause=error)
        
        elif "connection" in error_str or "network" in error_str or "timeout" in error_str:
            return NetworkError(str(error), context=context, cause=error)
        
        elif "import" in error_str or "module" in error_str or "not found" in error_str:
            return DependencyError(str(error), context=context, cause=error)
        
        elif "config" in error_str or "setting" in error_str or "key" in error_str:
            return ConfigurationError(str(error), context=context, cause=error)
        
        elif "validation" in error_str or "invalid" in error_str or "format" in error_str:
            return ValidationError(str(error), context=context, cause=error)
        
        else:
            # Default to internal error
            return PlanDayError(str(error), context=context, cause=error)
    
    def _record_error(self, error: PlanDayError):
        """Record error in history"""
        self.error_history.append(error)
        
        # Maintain history size limit
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def _log_error(self, error: PlanDayError):
        """Log error with appropriate level"""
        log_data = error.to_dict()
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error occurred", **log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error("High severity error occurred", **log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error occurred", **log_data)
        else:
            logger.info("Low severity error occurred", **log_data)
    
    def _attempt_recovery(self, error: PlanDayError) -> bool:
        """Attempt to recover from the error using registered strategies"""
        strategies = self.recovery_strategies.get(error.category, [])
        
        for strategy in strategies:
            try:
                if strategy(error):
                    logger.info("Error recovery successful", 
                               error_category=error.category.value,
                               strategy=strategy.__name__)
                    return True
            except Exception as recovery_error:
                logger.warning("Recovery strategy failed", 
                             error_category=error.category.value,
                             strategy=strategy.__name__,
                             recovery_error=str(recovery_error))
        
        return False
    
    def _generate_user_response(self, error: PlanDayError, recovery_success: bool) -> str:
        """Generate user-friendly error message"""
        base_messages = {
            ErrorCategory.AUTHENTICATION: "🔒 Permission issue: Please check your system permissions for Calendar and Reminders access.",
            ErrorCategory.NETWORK: "🌐 Connection issue: Please check your internet connection and try again.",
            ErrorCategory.DEPENDENCY: "⚙️ System component issue: Some features may be temporarily unavailable.",
            ErrorCategory.CONFIGURATION: "🔧 Configuration issue: Please check your system setup.",
            ErrorCategory.USER_INPUT: "❓ Input issue: Please check your input and try again.",
            ErrorCategory.DATA: "📊 Data processing issue: There was a problem processing your request.",
            ErrorCategory.SYSTEM: "💻 System issue: A technical problem occurred.",
            ErrorCategory.INTERNAL: "🔧 Internal error: Something went wrong internally."
        }
        
        user_message = base_messages.get(error.category, "An unexpected error occurred.")
        
        # Add recovery status
        if recovery_success:
            user_message += " The issue has been automatically resolved."
        else:
            user_message += " Please try again or contact support if the problem persists."
        
        # Add specific guidance for common errors
        if error.category == ErrorCategory.AUTHENTICATION and "Calendar" in error.message:
            user_message += "\n\nTo fix this:\n1. Open System Settings > Privacy & Security > Calendar\n2. Enable access for Terminal or your Python app\n3. Restart the application"
        
        return user_message
    
    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable[[PlanDayError], bool]):
        """Register a recovery strategy for a specific error category"""
        if category not in self.recovery_strategies:
            self.recovery_strategies[category] = []
        self.recovery_strategies[category].append(strategy)
        
        logger.info("Recovery strategy registered", 
                   category=category.value, 
                   strategy=strategy.__name__)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        if not self.error_history:
            return {"total_errors": 0}
        
        stats = {
            "total_errors": len(self.error_history),
            "by_category": {},
            "by_severity": {},
            "recent_errors": len([e for e in self.error_history 
                                if (datetime.now() - e.timestamp).total_seconds() < 3600])
        }
        
        for error in self.error_history:
            # Category stats
            category = error.category.value
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0
            stats["by_category"][category] += 1
            
            # Severity stats
            severity = error.severity.value
            if severity not in stats["by_severity"]:
                stats["by_severity"][severity] = 0
            stats["by_severity"][severity] += 1
        
        return stats


# Global error handler instance
error_handler = ErrorHandler()


# Decorator for automatic error handling
def handle_errors(category: Optional[ErrorCategory] = None):
    """Decorator to automatically handle errors in functions"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],  # Limit context size
                    "kwargs": str(kwargs)[:200]
                }
                if category:
                    # Convert to specific error type
                    if category == ErrorCategory.DEPENDENCY:
                        raise DependencyError(str(e), context=context, cause=e)
                    elif category == ErrorCategory.CONFIGURATION:
                        raise ConfigurationError(str(e), context=context, cause=e)
                    # Add more specific mappings as needed
                
                # Re-raise as is if no specific category
                raise
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],
                    "kwargs": str(kwargs)[:200]
                }
                if category:
                    # Convert to specific error type
                    if category == ErrorCategory.DEPENDENCY:
                        raise DependencyError(str(e), context=context, cause=e)
                    elif category == ErrorCategory.CONFIGURATION:
                        raise ConfigurationError(str(e), context=context, cause=e)
                
                raise
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Recovery strategies
def calendar_permission_recovery(error: PlanDayError) -> bool:
    """Recovery strategy for Calendar permission issues"""
    if "Calendar access not granted" in error.message:
        logger.info("Attempting calendar permission recovery")
        # Could attempt to re-initialize calendar connection
        # For now, just return False as this requires user action
        return False
    return False


def network_retry_recovery(error: PlanDayError) -> bool:
    """Recovery strategy for network issues"""
    if error.category == ErrorCategory.NETWORK:
        logger.info("Attempting network recovery")
        # Could implement retry logic here
        # For now, just log and return False
        return False
    return False


# Register default recovery strategies
error_handler.register_recovery_strategy(ErrorCategory.AUTHENTICATION, calendar_permission_recovery)
error_handler.register_recovery_strategy(ErrorCategory.NETWORK, network_retry_recovery)


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    return error_handler