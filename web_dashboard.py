#!/usr/bin/env python3
"""
Web Dashboard Entry Point

Start the Flask web dashboard for the AI Attendance System.
Dashboard can be accessed at: http://localhost:5000

Features:
- View today's attendance
- View all attendance records with date filtering
- View student list with enrollment status
- Download attendance records as CSV
- Real-time statistics and metrics
"""

import sys
import os
import webbrowser
from pathlib import Path
from threading import Timer

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from frontend.web.app import create_app


def open_browser(url: str, delay: float = 2.0) -> None:
    """Open browser after server starts."""
    def _open():
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Note: Could not open browser automatically: {e}")
    
    Timer(delay, _open).start()


def main():
    """Start the Flask web dashboard."""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   AI Attendance System - Web Dashboard                     ║
    ║                                                            ║
    ║   Web Interface: http://localhost:5000                    ║
    ║   Dashboard:    http://localhost:5000/                    ║
    ║   Records:      http://localhost:5000/records             ║
    ║   Students:     http://localhost:5000/students            ║
    ║   Download CSV: http://localhost:5000/download-csv        ║
    ║                                                            ║
    ║   Press CTRL+C to stop the server                         ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Create app
    app = create_app()
    
    # Open browser
    try:
        open_browser("http://localhost:5000", delay=2.0)
    except Exception as e:
        print(f"Note: Could not open browser: {e}")
    
    # Run server
    try:
        app.run(
            debug=False,
            host='0.0.0.0',
            port=5000,
            use_reloader=False,
            use_debugger=False
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped gracefully")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
