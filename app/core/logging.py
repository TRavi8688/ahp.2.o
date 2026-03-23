import logging
import sys
import structlog
import re

SENSITIVE_KEYS = {"user_id", "uid", "patient_id", "email", "token", "apikey", "authorization", "password", "secret_key"}

def mask_sensitive_data(logger, method_name, event_dict):
    """Processor to mask PII and secrets in logs."""
    for key in SENSITIVE_KEYS:
        if key in event_dict:
            val = str(event_dict[key])
            if len(val) > 8:
                event_dict[key] = f"{val[:4]}...{val[-4:]}"
            else:
                event_dict[key] = "***"
    
    # Also mask content that looks like tokens or emails in 'event' message
    if "event" in event_dict:
        # Simple email mask
        event_dict["event"] = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL_REDACTED]", event_dict["event"])
    
    return event_dict

def setup_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            mask_sensitive_data,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

logger = structlog.get_logger()
