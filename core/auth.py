"""
Custom authentication backends.

CookieTokenAuthentication accepts the legacy DRF token from an httpOnly
cookie, but requires CSRF validation for unsafe cookie-authenticated requests.
Header-based Token authentication remains CSRF-independent.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


class CookieTokenAuthentication(TokenAuthentication):
    """Authenticate by Authorization header or the httpOnly token cookie."""

    def authenticate(self, request):
        auth = super().authenticate(request)
        if auth is not None:
            return auth

        token_key = request.COOKIES.get("token")
        if not token_key:
            return None

        try:
            token = Token.objects.select_related("user").get(key=token_key)
        except Token.DoesNotExist:
            raise AuthenticationFailed(_("Invalid token."))

        if not token.user.is_active:
            raise AuthenticationFailed(_("User inactive or deleted."))

        # Cookies are sent automatically by browsers, so unsafe requests
        # must pass Django CSRF validation.
        SessionAuthentication().enforce_csrf(request)

        return (token.user, token)
