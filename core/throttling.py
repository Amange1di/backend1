from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def is_local_request(request) -> bool:
    try:
        host = request.get_host().split(":")[0].strip("[]").lower()
    except Exception:
        return False

    return host in LOCAL_HOSTS


class LocalAwareAnonRateThrottle(AnonRateThrottle):
    """Keep production throttling, but do not rate-limit local E2E/dev traffic."""

    def allow_request(self, request, view):
        if is_local_request(request):
            return True

        return super().allow_request(request, view)


class LocalAwareUserRateThrottle(UserRateThrottle):
    """Keep production throttling, but do not rate-limit local E2E/dev traffic."""

    def allow_request(self, request, view):
        if is_local_request(request):
            return True

        return super().allow_request(request, view)
