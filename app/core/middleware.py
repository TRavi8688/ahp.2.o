from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.redis_service import redis_service
from app.core.logging import logger
import json
import uuid
import structlog
import asyncio

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Enterprise Traceability: Injects a unique X-Request-ID and enforces IP containment."""
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        from app.core.limiter import check_ip_blacklist
        if await check_ip_blacklist(client_ip):
            logger.warning("BLACKLIST_HIT", ip=client_ip)
            return Response(status_code=403, content="Access Denied")

        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    GOOGLE-GRADE IDEMPOTENCY: 
    1. Response Replay: Replays cached responses for duplicate keys.
    2. Thundering Herd Protection: Uses Redis locks to prevent concurrent execution of the same key.
    """
    async def dispatch(self, request: Request, call_next):
        if request.method not in ["POST", "PATCH", "PUT"]:
            return await call_next(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        user_id = request.scope.get("user", {}).get("id", "anon")
        cache_key = f"idempotency:res:{user_id}:{idempotency_key}"
        lock_key = f"idempotency:lock:{user_id}:{idempotency_key}"

        try:
            # 1. Check for cached response
            cached_res = await redis_service.get(cache_key)
            if cached_res:
                logger.info("IDEMPOTENCY_HIT", key=idempotency_key)
                data = json.loads(cached_res)
                return Response(
                    content=data["body"],
                    status_code=data["status_code"],
                    headers=data["headers"],
                    media_type=data.get("media_type", "application/json")
                )

            # 2. Distributed Locking (Prevent Thundering Herd)
            # Try to acquire lock for 30s
            is_locked = await redis_service.set(lock_key, "LOCKED", expire=30, nx=True)
            if not is_locked:
                logger.warning("IDEMPOTENCY_CONCURRENT_WAIT", key=idempotency_key)
                # Wait and retry cache lookup a few times (Adaptive Polling)
                for _ in range(5):
                    await asyncio.sleep(1.0)
                    cached_res = await redis_service.get(cache_key)
                    if cached_res:
                        data = json.loads(cached_res)
                        return Response(content=data["body"], status_code=data["status_code"], headers=data["headers"])
                
                return Response(status_code=409, content=json.dumps({"detail": "Operation in progress"}), media_type="application/json")

            # 3. Process Request
            response = await call_next(request)

            # 4. Cache and Release
            if 200 <= response.status_code < 300:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                new_response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

                cache_data = {
                    "body": response_body.decode('utf-8') if response.media_type == "application/json" else "",
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type
                }
                
                if cache_data["body"]:
                    await redis_service.set(cache_key, json.dumps(cache_data), expire=86400)
                
                return new_response

            return response

        except Exception as e:
            logger.error("IDEMPOTENCY_SYSTEM_ERROR", error=str(e))
            return await call_next(request)
        finally:
            # Always release the lock
            await redis_service.delete(lock_key)
