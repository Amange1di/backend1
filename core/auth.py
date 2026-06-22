"""
Custom authentication backends.

CookieTokenAuthentication — проверяет httpOnly cookie 'token' в дополнение
к стандартному Authorization: Token xxx заголовку.
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed


class CookieTokenAuthentication(TokenAuthentication):
    """
    Token authentication that also checks the 'token' httpOnly cookie.
    Falls back to the cookie if no Authorization header is provided.
    This allows XSS-protected authentication via httpOnly cookies
    while maintaining backward compatibility with the Authorization header.
    """

    def authenticate(self, request):
        # First try standard header-based auth (Authorization: Token xxx)
        auth = super().authenticate(request)
        if auth is not None:
            return auth

        # Fallback to httpOnly cookie
        token_key = request.COOKIES.get("token")
        if not token_key:
            return None

        try:
            token = Token.objects.get(key=token_key)
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid token.")

        return (token.user, token)
