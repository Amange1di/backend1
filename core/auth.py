"""
Custom authentication backends with first-login restrictions.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied


FIRST_LOGIN_ALLOWED_PATHS = {
    "/api/auth/me/",
    "/api/auth/logout/",
    "/api/auth/first-login/set-password/",
    "/api/auth/student/set-password/",
}


def _enforce_first_login_scope(request, user):
    if (
        user.must_set_password
        and request.path not in FIRST_LOGIN_ALLOWED_PATHS
    ):
        raise PermissionDenied(
            _(
                "You must set your own password "
                "before using the application."
            )
        )


class RestrictedTokenAuthentication(TokenAuthentication):
    """DRF token auth with a restricted first-login session."""

    def authenticate(self, request):
        auth = super().authenticate(request)
        if auth is None:
            return None
        user, token = auth
        _enforce_first_login_scope(request, user)
        return user, token


class CookieTokenAuthentication(RestrictedTokenAuthentication):
    """Authenticate by Authorization header or httpOnly token cookie."""

    def authenticate(self, request):
        auth = TokenAuthentication.authenticate(self, request)
        if auth is not None:
            user, token = auth
            _enforce_first_login_scope(request, user)
            return user, token

        token_key = request.COOKIES.get("token")
        if not token_key:
            return None

        try:
            token = Token.objects.select_related("user").get(key=token_key)
        except Token.DoesNotExist:
            raise AuthenticationFailed(_("Invalid token."))

        if not token.user.is_active:
            raise AuthenticationFailed(_("User inactive or deleted."))

        SessionAuthentication().enforce_csrf(request)
        _enforce_first_login_scope(request, token.user)

        return token.user, token
