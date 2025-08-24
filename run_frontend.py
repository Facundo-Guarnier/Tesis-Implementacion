#!/usr/bin/env python3
"""
Frontend Configuration Manager for Traffic System

Entry point script for the Streamlit-based configuration frontend.
Provides web interface for managing config.yaml and controlling services.

Usage:
    poetry run streamlit run run_frontend.py

    # With custom port
    poetry run streamlit run run_frontend.py --server.port 8502

    # With debug mode
    poetry run streamlit run run_frontend.py --logger.level debug

Features:
    - Configuration editing with real-time validation
    - Service management and monitoring
    - Backup and restore functionality
    - Performance monitoring and alerts
    - Comprehensive error handling
"""

import logging
import os
import sys
from pathlib import Path

# Configure UTF-8 encoding for Windows console (only when not running with Streamlit)
if sys.platform == "win32" and "streamlit" not in sys.modules:
    try:
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    except (AttributeError, ValueError):
        # If streams are already detached or not available, skip encoding setup
        pass

# Add project root to path for imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Environment setup
os.environ.setdefault("STREAMLIT_LOGGER_LEVEL", "INFO")
os.environ.setdefault("STREAMLIT_CLIENT_SHOW_ERROR_DETAILS", "true")
os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")

# Configure logging with enhanced format and UTF-8 encoding
log_handlers = []

# Console handler with UTF-8 encoding
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
log_handlers.append(console_handler)

# File handler if logs directory exists
if Path("logs").exists():
    file_handler = logging.FileHandler("logs/frontend.log", mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    log_handlers.append(file_handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger("ConfigFrontend")


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    if sys.version_info < (3, 11):
        logger.error(f"❌ Python 3.11+ requerido. Versión actual: {sys.version}")
        logger.error("💡 Actualiza Python a la versión 3.11 o superior")
        return False

    logger.info(f"✅ Python {sys.version.split()[0]} compatible")
    return True


def check_poetry_available() -> bool:
    """Check if Poetry is available."""
    try:
        import subprocess

        result = subprocess.run(
            ["poetry", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            logger.info(f"✅ Poetry disponible: {result.stdout.strip()}")
            return True
        else:
            logger.error("❌ Poetry no responde correctamente")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Check if we're running in a debugging context (VS Code, etc.)
        if any(
            debug_indicator in str(sys.argv)
            for debug_indicator in ["debugpy", "ptvsd", "--debug"]
        ):
            logger.warning("⚠️ Poetry no encontrado en PATH (contexto de debugging)")
            logger.info("💡 Continuando sin verificación de Poetry en modo debug")
            return True
        else:
            logger.error("❌ Poetry no encontrado en PATH")
            logger.error(
                "💡 Instala Poetry: https://python-poetry.org/docs/#installation"
            )
            return False
    except Exception as e:
        logger.error(f"❌ Error verificando Poetry: {e}")
        return False


def check_dependencies() -> bool:
    """Check if all required dependencies are available."""
    required_packages = [
        ("streamlit", "Streamlit web framework"),
        ("yaml", "YAML configuration parser"),
        ("psutil", "Process monitoring"),
        ("pydantic", "Data validation"),
    ]

    missing_packages = []

    for package, description in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append((package, description))

    if missing_packages:
        logger.error("❌ Dependencias faltantes:")
        for package, description in missing_packages:
            logger.error(f"   • {package}: {description}")
        logger.error("💡 Ejecuta: poetry install")
        return False

    logger.info("✅ Dependencias principales verificadas")
    return True


def check_configuration() -> bool:
    """Check if configuration files exist and are accessible."""
    try:
        config_path = project_root / "config.yaml"

        if not config_path.exists():
            logger.warning(f"⚠️ Archivo de configuración no encontrado: {config_path}")
            logger.info("💡 Se creará una configuración por defecto")
            return True  # Allow startup, will create default config

        # Try to read the config
        import yaml

        with open(config_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            logger.warning("⚠️ Archivo de configuración vacío")
            return True  # Allow startup

        logger.info("✅ Configuración verificada")
        return True

    except Exception as e:
        logger.error(f"❌ Error verificando configuración: {e}")
        return False


def setup_directories() -> None:
    """Create necessary directories if they don't exist."""
    directories = ["logs", "backups", "temp"]

    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Directorio creado: {dir_path}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo crear directorio {dir_path}: {e}")


def show_system_info() -> None:
    """Show system information for debugging."""
    try:
        import platform

        logger.info(f"🖥️ Sistema: {platform.system()} {platform.release()}")
        logger.info(f"🐍 Python: {sys.version.split()[0]}")
        logger.info(f"📁 Directorio de trabajo: {os.getcwd()}")

        # Show environment variables relevant to Streamlit
        streamlit_vars = {
            k: v for k, v in os.environ.items() if k.startswith("STREAMLIT_")
        }
        if streamlit_vars:
            logger.info("🔧 Variables de entorno Streamlit:")
            for key, value in streamlit_vars.items():
                logger.info(f"   {key}={value}")

    except Exception as e:
        logger.warning(f"⚠️ Error obteniendo información del sistema: {e}")


def show_startup_info() -> None:
    """Show startup information and instructions."""
    logger.info("=" * 60)
    logger.info("🚦 SISTEMA DE CONFIGURACIÓN DE TRÁFICO INTELIGENTE")
    logger.info("=" * 60)
    logger.info("🚀 Iniciando Frontend de Configuración...")
    logger.info(f"📁 Directorio del proyecto: {project_root}")
    logger.info("📱 Interfaz web disponible en: http://localhost:8501")
    logger.info("")
    logger.info("🔧 Funcionalidades disponibles:")
    logger.info("   • Edición de configuración con validación en tiempo real")
    logger.info("   • Gestión y monitoreo de servicios")
    logger.info("   • Sistema de backups y restauración")
    logger.info("   • Alertas de rendimiento y monitoreo")
    logger.info("   • Log de auditoría de cambios")
    logger.info("")
    logger.info("💡 Comandos útiles:")
    logger.info("   • Ctrl+C para detener el servidor")
    logger.info("   • F5 para recargar la página web")
    logger.info("   • Revisa los logs en tiempo real aquí")
    logger.info("=" * 60)


def parse_arguments() -> dict[str, str]:
    """Parse command line arguments for Streamlit configuration."""
    args = {}

    # Simple argument parsing for common Streamlit options
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith("--server.port"):
            if "=" in arg:
                args["port"] = arg.split("=", 1)[1]
            elif i < len(sys.argv) - 1:
                args["port"] = sys.argv[i + 1]
        elif arg.startswith("--logger.level"):
            if "=" in arg:
                args["log_level"] = arg.split("=", 1)[1]
            elif i < len(sys.argv) - 1:
                args["log_level"] = sys.argv[i + 1]
        elif arg == "--help" or arg == "-h":
            args["help"] = "true"

    return args


def show_help() -> None:
    """Show help information."""
    print(
        """
🚦 Sistema de Configuración de Tráfico Inteligente - Frontend

Uso:
    poetry run streamlit run run_frontend.py [opciones]

Opciones comunes de Streamlit:
    --server.port PORT          Puerto del servidor (por defecto: 8501)
    --server.address ADDRESS    Dirección del servidor (por defecto: localhost)
    --logger.level LEVEL        Nivel de logging (debug, info, warning, error)
    --server.headless true      Ejecutar sin abrir navegador automáticamente
    --help, -h                  Mostrar esta ayuda

Ejemplos:
    # Ejecutar en puerto personalizado
    poetry run streamlit run run_frontend.py --server.port 8502

    # Ejecutar con logging debug
    poetry run streamlit run run_frontend.py --logger.level debug

    # Ejecutar sin abrir navegador
    poetry run streamlit run run_frontend.py --server.headless true

Para más opciones de Streamlit:
    streamlit run --help
    """
    )


def main_with_error_handling() -> None:
    """Main function with comprehensive error handling."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Show help if requested
        if args.get("help"):
            show_help()
            return

        # Pre-flight checks
        logger.info("🔍 Ejecutando verificaciones previas...")

        if not check_python_version():
            logger.error("❌ Verificación de Python falló")
            sys.exit(1)

        if not check_poetry_available():
            logger.error("❌ Verificación de Poetry falló")
            sys.exit(1)

        if not check_dependencies():
            logger.error("❌ Verificación de dependencias falló")
            sys.exit(1)

        if not check_configuration():
            logger.error("❌ Verificación de configuración falló")
            sys.exit(1)

        # Setup
        setup_directories()
        show_system_info()
        show_startup_info()

        # Import and run main app
        from src.traffic_system.frontend.app import main

        logger.info("🎯 Iniciando aplicación Streamlit...")
        main()

    except KeyboardInterrupt:
        logger.info("⏹️ Aplicación detenida por el usuario")

    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        logger.error("💡 Verifica que todas las dependencias estén instaladas:")
        logger.error("   poetry install")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Error crítico en el frontend: {e}", exc_info=True)
        logger.error("🚨 La aplicación se cerrará debido al error crítico")

        # Try to save any pending changes before exit
        try:
            logger.info("💾 Intentando guardar cambios pendientes...")
            # This would be handled by the app's cleanup logic
        except Exception:
            pass

        # Don't call sys.exit in Streamlit context, just log the error


if __name__ == "__main__":
    main_with_error_handling()
