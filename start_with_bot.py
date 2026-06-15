#!/usr/bin/env python
"""
Start Django with Telegram bot running in a background thread.
For use on Render Web Service (single process deployment).
"""

import os
import sys
import threading
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_telegram_bot():
    """Run Telegram bot in a background thread."""
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        
        # Load .env if available
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        import django
        django.setup()
        
        from telegram_bot.bot import run_bot
        run_bot()
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Start Gunicorn with Telegram bot in background."""
    # Start Telegram bot in background thread
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    logger.info("Telegram bot thread started")
    
    # Import and run Gunicorn
    from gunicorn.app.wsgiapp import run
    
    # Gunicorn config
    config = {
        'bind': f'0.0.0.0:{os.environ.get("PORT", 8000)}',
        'workers': 2,
        'accesslog': '-',
        'errorlog': '-',
    }
    
    logger.info("Starting Gunicorn web server...")
    
    # Run Gunicorn with WSGI app
    sys.argv[1:] = [
        'config.wsgi:application',
        '--bind', f'0.0.0.0:{os.environ.get("PORT", 8000)}',
        '--workers', '2',
    ]
    
    run()


if __name__ == "__main__":
    main()
