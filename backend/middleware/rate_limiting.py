"""
Rate Limiting Middleware for PCF Calculator Backend

TASK-BE-P7-020: Rate limiting middleware with per-endpoint limits.

Implements rate limiting to protect API endpoints from abuse:
- General endpoints: 100 requests/minute
- Calculation endpoints: 10 requests/minute
- Auth endpoints: 5 attempts/5 minutes (brute force protection)
- Admin users: 10x higher limits

Features:
- Per-client tracking (by IP or user ID)
- Memory storage (default) or Redis (distributed)
- RFC-compliant rate limit headers
- 429 Too Many Requests with Retry-After

Reference: RFC 6585 (429 status), IETF draft-polli-ratelimit-headers
"""

import base64
import json
import logging
import threading
import time
from typing import Any, Callable, Optional

from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


class MemoryStorage:
    """
    In-memory storage backend for rate limiting.

    Thread-safe storage using dictionary with automatic expiration.
    Suitable for single-instance deployments.

    Attributes:
        _data: Dictionary storing {key: (count, reset_time)}
        _lock: Threading lock for thread safety
    """

    def __init__(self):
        """Initialize memory storage."""
        self._data: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def get_count(self, key: str) -> int:
        """
        Get current request count for a key.

        Args:
            key: Rate limit key (client identifier)

        Returns:
            Current count, or 0 if key doesn't exist or is expired
        """
        with self._lock:
            if key not in self._data:
                return 0

            count, reset_time = self._data[key]

            # Check if expired
            if time.time() >= reset_time:
                del self._data[key]
                return 0

            return count

    def increment(self, key: str, window_seconds: int) -> int:
        """
        Increment request count for a key.

        Args:
            key: Rate limit key (client identifier)
            window_seconds: Time window for rate limiting

        Returns:
            New count after increment
        """
        with self._lock:
            current_time = time.time()

            if key in self._data:
                count, reset_time = self._data[key]

                # Check if window expired
                if current_time >= reset_time:
                    # Reset window
                    new_reset = current_time + window_seconds
                    self._data[key] = (1, new_reset)
                    return 1
                else:
                    # Increment within window
                    new_count = count + 1
                    self._data[key] = (new_count, reset_time)
                    return new_count
            else:
                # New key
                reset_time = current_time + window_seconds
                self._data[key] = (1, reset_time)
                return 1

    def get_reset_time(self, key: str) -> int:
        """
        Get reset timestamp for a key.

        Args:
            key: Rate limit key (client identifier)

        Returns:
            Unix timestamp when the rate limit resets
        """
        with self._lock:
            if key in self._data:
                _, reset_time = self._data[key]
                return int(reset_time)
            return int(time.time())

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from storage.

        Returns:
            Number of entries cleaned up
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                k for k, (_, reset_time) in self._data.items()
                if current_time >= reset_time
            ]
            for key in expired_keys:
                del self._data[key]
            return len(expired_keys)


class RedisStorage:
    """
    Redis-based storage backend for rate limiting.

    Suitable for distributed deployments with multiple instances.
    Uses Redis INCR with TTL for atomic operations.

    Attributes:
        _client: Redis client instance
    """

    def __init__(self, client: Any):
        """
        Initialize Redis storage.

        Args:
            client: Redis client instance
        """
        self._client = client

    def get_count(self, key: str) -> int:
        """
        Get current request count from Redis.

        Args:
            key: Rate limit key (client identifier)

        Returns:
            Current count, or 0 if key doesn't exist
        """
        try:
            value = self._client.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.warning(f"Redis get_count failed: {e}")
            return 0

    def increment(self, key: str, window_seconds: int) -> int:
        """
        Increment request count in Redis with TTL.

        Args:
            key: Rate limit key (client identifier)
            window_seconds: Time window for rate limiting

        Returns:
            New count after increment
        """
        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            results = pipe.execute()

            count = results[0]
            ttl = results[1]

            # Set expiration if this is a new key (TTL is -1 if not set)
            if ttl == -1:
                self._client.expire(key, window_seconds)

            return count
        except Exception as e:
            logger.warning(f"Redis increment failed: {e}")
            return 1

    def get_reset_time(self, key: str) -> int:
        """
        Get reset timestamp from Redis TTL.

        Args:
            key: Rate limit key (client identifier)

        Returns:
            Unix timestamp when the rate limit resets
        """
        try:
            ttl = self._client.ttl(key)
            if ttl > 0:
                return int(time.time()) + ttl
            return int(time.time())
        except Exception as e:
            logger.warning(f"Redis get_reset_time failed: {e}")
            return int(time.time())


def get_storage(redis_url: Optional[str] = None) -> MemoryStorage | RedisStorage:
    """
    Get storage backend based on configuration.

    Args:
        redis_url: Optional Redis URL for distributed storage

    Returns:
        MemoryStorage or RedisStorage instance
    """
    if redis_url:
        try:
            import redis
            client = redis.from_url(redis_url)
            client.ping()  # Test connection
            logger.info("Using Redis storage for rate limiting")
            return RedisStorage(client)
        except Exception as e:
            logger.warning(f"Redis connection failed, falling back to memory: {e}")

    logger.info("Using memory storage for rate limiting")
    return MemoryStorage()


def get_rate_limit_storage() -> MemoryStorage:
    """
    Get the default rate limit storage instance.

    Returns:
        MemoryStorage instance
    """
    return MemoryStorage()


def get_client_ip(scope: Scope) -> str:
    """
    Extract client IP address from request scope.

    Respects X-Forwarded-For header for proxied requests.

    Args:
        scope: ASGI scope

    Returns:
        Client IP address string
    """
    headers = Headers(scope=scope)

    # Check X-Forwarded-For header (from load balancer/proxy)
    forwarded_for = headers.get("x-forwarded-for")
    if forwarded_for:
        # Take first IP (client IP) from comma-separated list
        return forwarded_for.split(",")[0].strip()

    # Fall back to direct client connection
    client = scope.get("client")
    if client:
        return client[0]

    return "unknown"


def get_user_from_token(headers: Headers) -> Optional[str]:
    """
    Extract user ID from JWT token in Authorization header.

    Args:
        headers: Request headers

    Returns:
        User ID if authenticated, None otherwise
    """
    auth_header = headers.get("authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    try:
        # Extract token
        token = auth_header[7:]

        # Decode JWT payload (without verification - just for ID extraction)
        # The auth middleware handles actual verification
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # Decode payload (middle part)
        payload_b64 = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("sub")
    except Exception:
        return None


def is_admin_request(headers: Headers) -> bool:
    """
    Check if request is from an admin user.

    Args:
        headers: Request headers

    Returns:
        True if admin, False otherwise
    """
    # Check X-Admin header (for testing/internal)
    if headers.get("x-admin", "").lower() == "true":
        return True

    # Check JWT token for admin role
    auth_header = headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header[7:]
            parts = token.split(".")
            if len(parts) == 3:
                payload_b64 = parts[1]
                padding = 4 - len(payload_b64) % 4
                if padding != 4:
                    payload_b64 += "=" * padding
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                # Check for admin role in token
                return payload.get("role") == "admin" or payload.get("is_admin", False)
        except Exception:
            pass

    return False


class RateLimitMiddleware:
    """
    ASGI Middleware for rate limiting.

    Implements rate limiting with:
    - Per-client tracking (by IP or user ID)
    - Different limits per endpoint category
    - Admin user multiplier
    - RFC-compliant response headers

    Args:
        app: ASGI application
        storage: Storage backend (MemoryStorage or RedisStorage)
        default_limit: Default requests per window (default: 100)
        window_seconds: Default time window in seconds (default: 60)
        endpoint_limits: Dict of endpoint path -> limit override
        endpoint_windows: Dict of endpoint path -> window override
        endpoint_error_messages: Dict of endpoint path -> custom error message
        admin_multiplier: Multiplier for admin rate limits (default: 10)
        excluded_paths: Paths to exclude from rate limiting
    """

    def __init__(
        self,
        app: ASGIApp,
        storage: Optional[MemoryStorage | RedisStorage] = None,
        default_limit: int = 100,
        window_seconds: int = 60,
        endpoint_limits: Optional[dict[str, int]] = None,
        endpoint_windows: Optional[dict[str, int]] = None,
        endpoint_error_messages: Optional[dict[str, str]] = None,
        admin_multiplier: int = 10,
        excluded_paths: Optional[list[str]] = None,
    ):
        """Initialize rate limit middleware."""
        self.app = app
        self.storage = storage or MemoryStorage()
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.endpoint_limits = endpoint_limits or {}
        self.endpoint_windows = endpoint_windows or {}
        self.endpoint_error_messages = endpoint_error_messages or {}
        self.admin_multiplier = admin_multiplier
        self.excluded_paths = excluded_paths or ["/health", "/docs", "/openapi.json"]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process request through rate limiting middleware.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Skip excluded paths
        if self._is_excluded_path(path):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)

        # Get client identifier
        client_key = self._get_client_key(scope, headers)

        # Get endpoint-specific configuration
        limit = self._get_limit_for_path(path)
        window = self._get_window_for_path(path)

        # Apply admin multiplier
        if is_admin_request(headers):
            limit *= self.admin_multiplier

        # Build rate limit key
        rate_limit_key = f"rate_limit:{client_key}:{self._get_path_category(path)}"

        # Check and increment counter
        current_count = self.storage.increment(rate_limit_key, window)
        reset_time = self.storage.get_reset_time(rate_limit_key)
        remaining = max(0, limit - current_count)

        # Prepare rate limit headers
        rate_limit_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        # Check if rate limited
        if current_count > limit:
            retry_after = max(1, reset_time - int(time.time()))
            rate_limit_headers["Retry-After"] = str(retry_after)

            # Get custom error message if configured
            error_message = self.endpoint_error_messages.get(
                path, "Rate limit exceeded. Try again later."
            )

            response = JSONResponse(
                status_code=429,
                content={"detail": error_message},
                headers=rate_limit_headers,
            )
            await response(scope, receive, send)
            return

        # Wrap send to add headers to response
        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                response_headers = MutableHeaders(scope=message)
                for key, value in rate_limit_headers.items():
                    response_headers[key] = value
            await send(message)

        await self.app(scope, receive, send_with_headers)

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from rate limiting."""
        for excluded in self.excluded_paths:
            if path == excluded or path.startswith(excluded + "/"):
                return True
        return False

    def _get_client_key(self, scope: Scope, headers: Headers) -> str:
        """
        Get unique client identifier for rate limiting.

        Uses user ID for authenticated requests, IP for anonymous.

        Args:
            scope: ASGI scope
            headers: Request headers

        Returns:
            Client identifier string
        """
        # Try to get user ID from JWT
        user_id = get_user_from_token(headers)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        client_ip = get_client_ip(scope)
        return f"ip:{client_ip}"

    def _get_limit_for_path(self, path: str) -> int:
        """
        Get rate limit for a specific path.

        Args:
            path: Request path

        Returns:
            Rate limit for the path
        """
        # Check exact match first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]

        # Check prefix matches
        for endpoint_path, limit in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return limit

        return self.default_limit

    def _get_window_for_path(self, path: str) -> int:
        """
        Get time window for a specific path.

        Args:
            path: Request path

        Returns:
            Window in seconds for the path
        """
        # Check exact match first
        if path in self.endpoint_windows:
            return self.endpoint_windows[path]

        # Check prefix matches
        for endpoint_path, window in self.endpoint_windows.items():
            if path.startswith(endpoint_path):
                return window

        return self.window_seconds

    def _get_path_category(self, path: str) -> str:
        """
        Get category for a path (for separate counters).

        Args:
            path: Request path

        Returns:
            Category string for the path
        """
        # Check for endpoint-specific limits (separate counters)
        for endpoint_path in self.endpoint_limits:
            if path == endpoint_path or path.startswith(endpoint_path):
                return endpoint_path.replace("/", "_")

        return "general"
