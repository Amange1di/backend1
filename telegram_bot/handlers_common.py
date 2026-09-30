"""Compatibility facade for common Telegram handlers."""

from .handlers.common_menu import help_command, menu_back, menu_help
from .handlers.common_start import start
from .handlers.common_verification import get_message_handler, verify_code

__all__ = [
    "get_message_handler",
    "help_command",
    "menu_back",
    "menu_help",
    "start",
    "verify_code",
]
