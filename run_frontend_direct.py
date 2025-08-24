#!/usr/bin/env python3
"""
Direct Frontend Launcher for VS Code Debugging

This script launches the Streamlit frontend directly without relying on Poetry
being available in PATH, making it more suitable for VS Code debugging.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Set environment variables for Streamlit
os.environ.setdefault("STREAMLIT_LOGGER_LEVEL", "INFO")
os.environ.setdefault("STREAMLIT_CLIENT_SHOW_ERROR_DETAILS", "true")
os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")
os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")


def main() -> None:
    """Main entry point for direct frontend execution."""
    try:
        # Import and run Streamlit directly
        import streamlit.web.cli as stcli

        # Set up arguments for Streamlit
        sys.argv = [
            "streamlit",
            "run",
            str(project_root / "run_frontend.py"),
            "--server.port",
            "8501",
            "--server.headless",
            "true",
        ]

        # Run Streamlit
        stcli.main()

    except ImportError as e:
        print(f"❌ Error: Streamlit no está disponible: {e}")
        print("💡 Asegúrate de que el entorno virtual esté activado")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error ejecutando frontend: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
