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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True,
)
logger = logging.getLogger(__name__)


def main():
    """Start Gunicorn and Telegram bot as separate processes."""
    
    # Start Telegram bot as a separate process
    # NOTE: No PIPE — bot output goes directly to stdout/stderr so Render logs can see it
    bot_process = subprocess.Popen(
        [sys.executable, 'manage.py', 'run_bot'],
        stdout=None,
        stderr=None,
    )
    logger.info(f"Telegram bot process started (PID: {bot_process.pid})")
    
    # Set up signal handler to clean up bot process
    def cleanup(signum, frame):
        logger.info("Shutting down, terminating bot process...")
        try:
            bot_process.terminate()
            bot_process.wait(timeout=10)
        except Exception:
            bot_process.kill()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    # Run Gunicorn
    port = os.environ.get('PORT', '8000')
    logger.info(f"Starting Gunicorn web server on port {port}...")
    
    gunicorn_args = [
        'gunicorn',
        'config.wsgi:application',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '2',
        '--log-level', 'info',
    ]
    
    try:
        subprocess.run(gunicorn_args)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down bot process...")
        try:
            bot_process.terminate()
            bot_process.wait(timeout=10)
        except Exception:
            bot_process.kill()


if __name__ == "__main__":
    main()