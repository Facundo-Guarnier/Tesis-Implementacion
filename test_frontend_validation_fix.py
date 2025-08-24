#!/usr/bin/env python3
"""
Script para probar las correcciones de validación del frontend.
"""

import logging
import os
import sys
from pathlib import Path

# Añadir src al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_validation_fixes():
    """Probar las correcciones de validación del frontend."""
    print("🧪 Iniciando pruebas de validación del frontend...")
    
    try:
        # Importar las clases necesarias
        from src.traffic_system.frontend.utils.config_handler import ConfigHandler
        from src.traffic_system.frontend.utils.validation_utils import ValidationFeedbackUI
        
        # Crear instancias
        config_handler = ConfigHandler()
        validator = ValidationFeedbackUI(config_handler)
        
        # Cargar configuración actual
        print("📖 Cargando configuración actual...")
        config = config_handler.read_config()
        
        if not config:
            print("❌ No se pudo cargar la configuración")
            return False
            
        print(f"✅ Configuración cargada: {len(config)} secciones principales")
        
        # Pruebas específicas de validación de campos
        print("\n🔍 Probando validación de campos específicos...")
        
        test_cases = [
            # Casos que deberían pasar
            ("services.simulation_port", 5000, True, "Puerto válido"),
            ("reporte.generar", True, True, "Booleano válido"),
            ("reporte.steps", 60, True, "Entero positivo válido"),
            ("decision.decision", False, True, "Booleano válido"),
            ("sumo.simular", True, True, "Booleano válido"),
            
            # Casos que deberían fallar
            ("services.simulation_port", 80, False, "Puerto fuera de rango"),
            ("services.detection_port", "invalid", False, "Puerto no numérico"),
            ("reporte.generar", "true", False, "Booleano como string"),
            ("decision.steps", -1, False, "Entero negativo"),
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for field_path, value, should_pass, description in test_cases:
            print(f"\n📝 Probando: {field_path} = {value} ({description})")
            
            # Probar validación
            is_valid, error_msg = validator.validate_field(field_path, value, config)
            
            # Verificar resultado esperado
            if is_valid == should_pass:
                print(f"✅ PASS: Validación correcta para {field_path}")
                passed_tests += 1
            else:
                print(f"❌ FAIL: Validación incorrecta para {field_path}")
                print(f"   Esperado: {'válido' if should_pass else 'inválido'}")
                print(f"   Obtenido: {'válido' if is_valid else 'inválido'}")
                if error_msg:
                    print(f"   Error: {error_msg}")
        
        # Resumen de pruebas
        print(f"\n📊 Resumen de pruebas: {passed_tests}/{total_tests} pasaron")
        
        if passed_tests == total_tests:
            print("🎉 ¡Todas las pruebas de validación pasaron correctamente!")
            
            # Probar validación completa de configuración
            print("\n🔍 Probando validación completa de configuración...")
            is_valid, errors, warnings = validator.validate_full_config(config)
            
            if is_valid:
                print("✅ Configuración completa es válida")
                return True
            else:
                print(f"⚠️ Configuración tiene {len(errors)} errores:")
                for error in errors[:5]:  # Mostrar solo los primeros 5
                    print(f"   • {error}")
                if len(errors) > 5:
                    print(f"   ... y {len(errors) - 5} errores más")
                return False
        else:
            print("❌ Algunas pruebas de validación fallaron")
            return False
            
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        logger.exception("Error en pruebas de validación")
        return False

def test_config_save_load_cycle():
    """Probar el ciclo completo de guardar y cargar configuración."""
    print("\n💾 Probando ciclo de guardado y carga de configuración...")
    
    try:
        from src.traffic_system.frontend.utils.config_handler import ConfigHandler
        
        config_handler = ConfigHandler()
        
        # Cargar configuración original
        original_config = config_handler.read_config()
        
        # Hacer un pequeño cambio de prueba
        test_config = original_config.copy()
        test_config["test_timestamp"] = "test_frontend_validation_fix"
        
        print("📝 Guardando configuración de prueba...")
        success, errors = config_handler.validate_and_write_config(test_config)
        
        if not success:
            print(f"❌ Error guardando configuración: {errors}")
            return False
            
        print("✅ Configuración guardada exitosamente")
        
        # Cargar configuración y verificar
        print("📖 Recargando configuración...")
        reloaded_config = config_handler.read_config()
        
        if "test_timestamp" in reloaded_config:
            print("✅ Configuración recargada correctamente - cambios persistidos")
            
            # Limpiar el campo de prueba
            clean_config = reloaded_config.copy()
            del clean_config["test_timestamp"]
            
            # Restaurar configuración original
            config_handler.write_config(clean_config)
            print("🧹 Configuración limpiada y restaurada")
            
            return True
        else:
            print("❌ Los cambios no se persistieron correctamente")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de guardado/carga: {e}")
        logger.exception("Error en ciclo save/load")
        return False

if __name__ == "__main__":
    print("🚦 Pruebas de Frontend - Correcciones de Validación")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("config.yaml"):
        print("❌ No se encontró config.yaml - ejecutar desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Ejecutar pruebas
    validation_ok = test_validation_fixes()
    save_load_ok = test_config_save_load_cycle()
    
    print("\n" + "=" * 60)
    
    if validation_ok and save_load_ok:
        print("🎉 ¡Todas las pruebas pasaron! Las correcciones están funcionando.")
        sys.exit(0)
    else:
        print("❌ Algunas pruebas fallaron. Revisar los errores arriba.")
        sys.exit(1)
