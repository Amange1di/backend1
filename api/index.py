"""Vercel Python Runtime entry point for the Django application."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application


# Vercel's official Python Runtime discovers a WSGI or ASGI object named
# ``app`` from files inside ``api/``.
app = get_wsgi_application()
