#!/usr/bin/env python3
"""
Frontend Configuration Manager for Traffic System

Entry point script for the Streamlit-based configuration frontend.
Provides web interface for managing config.yaml and controlling services.

Usage:
    poetry run streamlit run run_frontend.py
"""

import logging
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.traffic_system.frontend.app import main

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ConfigFrontend")


if __name__ == "__main__":
    logger.info("🚀 Iniciando Frontend de Configuración del Sistema de Tráfico")
    logger.info("📱 Accede a la interfaz web en: http://localhost:8501")

    try:
        main()
    except Exception as e:
        logger.error(f"❌ Error crítico en el frontend: {e}", exc_info=True)
        # Don't call sys.exit in Streamlit context
