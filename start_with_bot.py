#!/usr/bin/env python
"""
Start Django with Telegram bot running as a separate process.
For use on Render Web Service (single process deployment).
"""

import os
import sys
import subprocess
import signal
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Start Gunicorn and Telegram bot as separate processes."""
    
    # Start Telegram bot as a separate process
    bot_process = subprocess.Popen(
        [sys.executable, 'manage.py', 'run_bot'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    logger.info(f"Telegram bot process started (PID: {bot_process.pid})")
    
    # Set up signal handler to clean up bot process
    def cleanup(signum, frame):
        logger.info("Shutting down, terminating bot process...")
        bot_process.terminate()
        bot_process.wait()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    # Run Gunicorn
    logger.info(f"Starting Gunicorn web server on port {os.environ.get('PORT', 8000)}...")
    
    gunicorn_args = [
        'gunicorn',
        'config.wsgi:application',
        '--bind', f'0.0.0.0:{os.environ.get("PORT", 8000)}',
        '--workers', '2',
    ]
    
    try:
        subprocess.run(gunicorn_args)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down bot process...")
        bot_process.terminate()
        bot_process.wait()


if __name__ == "__main__":
    main()