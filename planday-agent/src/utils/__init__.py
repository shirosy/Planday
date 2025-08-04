"""Utility functions for PlanDay agent system."""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """Set up structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set log level
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, log_level.upper())
    )


def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    
    config = {
        # API Keys
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        
        # Model Configuration
        "primary_model": os.getenv("PRIMARY_MODEL", "gpt-4o"),
        "backup_model": os.getenv("BACKUP_MODEL", "claude-3-5-sonnet-20241022"),
        "temperature": float(os.getenv("TEMPERATURE", "0.1")),
        
        # Agent Configuration
        "max_iterations": int(os.getenv("MAX_ITERATIONS", "10")),
        "memory_retention_days": int(os.getenv("MEMORY_RETENTION_DAYS", "30")),
        
        # Feature Flags
        "enable_image_parsing": os.getenv("ENABLE_IMAGE_PARSING", "true").lower() == "true",
        "enable_email_parsing": os.getenv("ENABLE_EMAIL_PARSING", "true").lower() == "true",
        "enable_smart_recommendations": os.getenv("ENABLE_SMART_RECOMMENDATIONS", "true").lower() == "true",
        
        # MCP Tool Paths
        "mcp_calendar_server_path": os.getenv("MCP_CALENDAR_SERVER_PATH", ""),
        "mcp_reminders_server_path": os.getenv("MCP_REMINDERS_SERVER_PATH", ""),
        
        # Logging
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_format": os.getenv("LOG_FORMAT", "json"),
    }
    
    return config


def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate configuration and return list of issues."""
    
    issues = []
    
    # Check required API keys
    if not config.get("openai_api_key") and not config.get("anthropic_api_key"):
        issues.append("At least one API key (OpenAI or Anthropic) must be configured")
    
    # Check MCP paths if features are enabled
    if config.get("enable_calendar_integration") and not config.get("mcp_calendar_server_path"):
        issues.append("Calendar integration enabled but MCP_CALENDAR_SERVER_PATH not configured")
    
    if config.get("enable_reminders_integration") and not config.get("mcp_reminders_server_path"):
        issues.append("Reminders integration enabled but MCP_REMINDERS_SERVER_PATH not configured")
    
    # Check numeric values
    try:
        temp = float(config.get("temperature", 0.1))
        if not 0 <= temp <= 2:
            issues.append("Temperature must be between 0 and 2")
    except (ValueError, TypeError):
        issues.append("Temperature must be a valid number")
    
    try:
        max_iter = int(config.get("max_iterations", 10))
        if max_iter < 1:
            issues.append("Max iterations must be at least 1")
    except (ValueError, TypeError):
        issues.append("Max iterations must be a valid integer")
    
    return issues


def format_time_natural(dt: datetime) -> str:
    """Format datetime in natural language."""
    
    now = datetime.now()
    today = now.date()
    
    # Get the date part
    if dt.date() == today:
        date_str = "today"
    elif dt.date() == today + timedelta(days=1):
        date_str = "tomorrow"
    elif dt.date() == today - timedelta(days=1):
        date_str = "yesterday"
    elif 1 <= (dt.date() - today).days <= 7:
        date_str = dt.strftime("%A")  # Day name
    else:
        date_str = dt.strftime("%B %d")  # Month Day
    
    # Get the time part
    time_str = dt.strftime("%-I:%M%p").lower()  # 3:30pm
    
    return f"{date_str} at {time_str}"


def parse_natural_time(time_str: str) -> Optional[datetime]:
    """Parse natural language time expressions."""
    
    time_str = time_str.lower().strip()
    now = datetime.now()
    
    # Handle relative dates
    if "today" in time_str:
        base_date = now.date()
    elif "tomorrow" in time_str:
        base_date = now.date() + timedelta(days=1)
    elif "yesterday" in time_str:
        base_date = now.date() - timedelta(days=1)
    elif "next week" in time_str:
        base_date = now.date() + timedelta(days=7)
    else:
        base_date = now.date()
    
    # Handle time patterns
    import re
    
    # 3pm, 3:30pm, etc.
    time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', time_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        period = time_match.group(3)
        
        if period == "pm" and hour < 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
        
        return datetime.combine(base_date, datetime.min.time().replace(hour=hour, minute=minute))
    
    # Default to current time on the base date
    return datetime.combine(base_date, now.time())


def estimate_task_duration(title: str, description: str = "") -> int:
    """Estimate task duration in minutes based on content."""
    
    # Base duration
    duration = 60  # 1 hour default
    
    # Adjust based on title length and complexity
    word_count = len(title.split()) + len(description.split())
    
    if word_count > 20:
        duration += 30  # Complex tasks take longer
    
    # Check for specific keywords
    quick_keywords = ["call", "email", "review", "check", "update"]
    long_keywords = ["develop", "research", "analyze", "create", "write", "design"]
    
    title_lower = title.lower()
    
    if any(keyword in title_lower for keyword in quick_keywords):
        duration = max(30, duration - 30)  # Quick tasks
    elif any(keyword in title_lower for keyword in long_keywords):
        duration += 60  # Long tasks
    
    # Check for time indicators in text
    if "quick" in title_lower or "brief" in title_lower:
        duration = max(15, duration // 2)
    elif "detailed" in title_lower or "thorough" in title_lower:
        duration *= 2
    
    return duration


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    
    import re
    
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)  # Remove control characters
    filename = filename.strip()
    
    # Ensure not empty
    if not filename:
        filename = "untitled"
    
    # Truncate if too long
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def safe_json_serialize(obj: Any) -> str:
    """Safely serialize object to JSON with datetime handling."""
    
    def json_serializer(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif hasattr(obj, 'model_dump'):  # Pydantic models
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    try:
        return json.dumps(obj, default=json_serializer, indent=2)
    except Exception:
        return json.dumps({"error": "Serialization failed", "type": str(type(obj))})


def create_session_id() -> str:
    """Create a unique session ID."""
    
    import uuid
    return str(uuid.uuid4())


def calculate_business_hours_between(start: datetime, end: datetime) -> float:
    """Calculate business hours between two datetimes."""
    
    business_start = 9  # 9 AM
    business_end = 17   # 5 PM
    
    current = start
    total_hours = 0.0
    
    while current.date() <= end.date():
        # Skip weekends
        if current.weekday() >= 5:  # Saturday = 5, Sunday = 6
            current = current.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            continue
        
        # Calculate business hours for this day
        day_start = max(current, current.replace(hour=business_start, minute=0, second=0, microsecond=0))
        day_end = min(end, current.replace(hour=business_end, minute=0, second=0, microsecond=0))
        
        if day_start < day_end:
            day_hours = (day_end - day_start).total_seconds() / 3600
            total_hours += day_hours
        
        # Move to next day
        current = current.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    return total_hours


def get_next_business_day(from_date: date, days: int = 1) -> date:
    """Get the next business day (excluding weekends)."""
    
    current = from_date
    business_days_found = 0
    
    while business_days_found < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            business_days_found += 1
    
    return current


# Export commonly used functions
__all__ = [
    "setup_logging",
    "load_config_from_env", 
    "validate_config",
    "format_time_natural",
    "parse_natural_time",
    "estimate_task_duration",
    "sanitize_filename",
    "safe_json_serialize",
    "create_session_id",
    "calculate_business_hours_between",
    "get_next_business_day"
]