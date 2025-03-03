#!/usr/bin/env python3
"""
Main entry point for the analytics dashboard.
Run this script to start the analytics visualization server.
"""
import os
import sys
import logging
from analytics.app import app

# Set up logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("analytics.main")
logging.getLogger('werkzeug').setLevel(logging.WARNING)


def main():
    """Start the analytics dashboard server."""
    try:
        port = int(os.environ.get('PORT', 8050))
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'

        logger.info("Starting Analytics Dashboard")
        logger.info(f"Server will run on port {port}")
        logger.info(f"Debug mode: {debug}")

        app.run_server(
            host='127.0.0.1',  # Make server accessible externally
            port=port,
            debug=debug
        )
    except Exception as e:
        logger.error(f"Failed to start analytics dashboard: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
