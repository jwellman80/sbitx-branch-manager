#!/usr/bin/env python3
"""
sBitx Branch Manager
Main entry point for the application

This tool allows testers to switch between different sBitx repositories
and branches, and build the selected version.
"""

import sys
import tkinter as tk
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.main_window import MainWindow


def main():
    """Main application entry point"""
    try:
        # Create and run the application
        app = MainWindow()
        app.mainloop()

    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
