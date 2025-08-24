#!/usr/bin/env python3
"""
Basic test script for the configuration frontend.

Tests core functionality without requiring Streamlit to be running.
"""

import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.traffic_system.frontend.utils.config_handler import ConfigHandler
from src.traffic_system.frontend.utils.service_manager import ServiceManager
from src.traffic_system.frontend.utils.validators import ConfigValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FrontendTest")


def test_config_handler() -> None:
    """Test configuration handler functionality."""
    logger.info("🧪 Testing ConfigHandler...")

    try:
        handler = ConfigHandler()

        # Test reading config
        config = handler.read_config()
        logger.info(f"✅ Config loaded with {len(config)} sections")

        # Test validation
        is_valid, errors = handler.validate_config_structure(config)
        if is_valid:
            logger.info("✅ Config structure is valid")
        else:
            logger.warning(f"⚠️ Config validation issues: {errors}")

        # Test backup listing
        backups = handler.list_backups()
        logger.info(f"✅ Found {len(backups)} existing backups")

    except Exception as e:
        logger.error(f"❌ ConfigHandler test failed: {e}")
        raise


def test_service_manager() -> None:
    """Test service manager functionality."""
    logger.info("🧪 Testing ServiceManager...")

    try:
        manager = ServiceManager()

        # Test service status
        services = manager.get_all_services_status()
        logger.info(f"✅ Found {len(services)} services")

        for name, status in services.items():
            status_text = "running" if status.is_running else "stopped"
            logger.info(f"  • {name}: {status_text}")

        # Test port conflicts
        conflicts = manager.get_port_conflicts()
        if conflicts:
            logger.warning(f"⚠️ Port conflicts detected: {conflicts}")
        else:
            logger.info("✅ No port conflicts detected")

        # Test system resources
        resources = manager.get_system_resources()
        logger.info(
            f"✅ System resources: CPU {resources['cpu_percent']:.1f}%, Memory {resources['memory_percent']:.1f}%"
        )

    except Exception as e:
        logger.error(f"❌ ServiceManager test failed: {e}")
        raise


def test_validator() -> None:
    """Test configuration validator."""
    logger.info("🧪 Testing ConfigValidator...")

    try:
        validator = ConfigValidator()
        handler = ConfigHandler()

        # Load current config
        config = handler.read_config()

        # Test full validation
        is_valid, errors, settings = validator.validate_full_config(config)

        if is_valid:
            logger.info("✅ Configuration validation passed")
        else:
            logger.warning(f"⚠️ Validation errors found: {len(errors)}")
            for error in errors[:3]:  # Show first 3 errors
                logger.warning(f"  • {error}")

        # Test field constraints
        constraints = validator.get_field_constraints("services.simulation_port")
        logger.info(f"✅ Field constraints example: {constraints}")

    except Exception as e:
        logger.error(f"❌ ConfigValidator test failed: {e}")
        raise


def main() -> None:
    """Run all tests."""
    logger.info("🚀 Starting frontend component tests...")

    tests = [
        ("ConfigHandler", test_config_handler),
        ("ServiceManager", test_service_manager),
        ("ConfigValidator", test_validator),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        try:
            test_func()
            results.append((test_name, True))
        except Exception as e:
            logger.error(f"❌ {test_name} test failed: {e}")
            results.append((test_name, False))

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("📊 Test Results Summary:")

    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  • {test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        logger.info("🎉 All tests passed! Frontend components are working correctly.")
        logger.info(
            "🚀 You can now run the frontend with: poetry run streamlit run run_frontend.py"
        )


if __name__ == "__main__":
    main()
