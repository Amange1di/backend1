"""Application-level rate limiting and security response headers."""

import ipaddress

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse


def _get_client_ip(request) -> str:
    """Return a normalized client IP without trusting a spoofable XFF prefix."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    candidates = [part.strip() for part in forwarded.split(",") if part.strip()]

    # Reverse proxies append the connecting address to X-Forwarded-For.
    # Using the right-most valid address prevents a client from bypassing
    # the limiter by changing the first value on every request.
    for candidate in reversed(candidates):
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            continue

    remote = request.META.get("REMOTE_ADDR", "")
    try:
        return str(ipaddress.ip_address(remote))
    except ValueError:
        return "unknown"


class RateLimitMiddleware:
    """Coarse IP limiter; DRF throttles still protect sensitive endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.excluded_paths = ["/admin/", "/api/docs/"]

    def __call__(self, request):
        if settings.DEBUG:
            return self.get_response(request)

        if any(request.path.startswith(path) for path in self.excluded_paths):
            return self.get_response(request)

        ip = _get_client_ip(request)
        cache_key = f"rate_limit:{ip}"

        if cache.add(cache_key, 1, timeout=60):
            request_count = 1
        else:
            try:
                request_count = cache.incr(cache_key)
            except (ValueError, NotImplementedError):
                request_count = cache.get(cache_key, 0) + 1
                cache.set(cache_key, request_count, 60)

        if request_count > 200:
            return JsonResponse(
                {"detail": "Слишком много запросов. Попробуйте позже."},
                status=429,
            )

        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        return response


class SecurityHeadersMiddleware:
    """Add browser security headers that are not emitted elsewhere."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
