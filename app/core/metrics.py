from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from fastapi import Request

# Google-Grade SLIs (Service Level Indicators)
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total", 
    "Total number of HTTP requests.",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Latency of HTTP requests in seconds.",
    ["method", "endpoint"]
)

ACTIVE_SESSIONS = Gauge(
    "active_sessions",
    "Number of active user sessions."
)

CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Current state of circuit breakers (0=Closed, 1=Open, 2=Half-Open)",
    ["provider"]
)

def instrument_request():
    """Middleware-style instrumentation for SLIs."""
    async def middleware(request: Request, call_next):
        start_time = time.time()
        
        # Route resolution for labeling
        endpoint = request.url.path
        method = request.method
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        status = response.status_code
        
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)
        
        return response
    
    return middleware
