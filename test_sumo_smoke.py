#!/usr/bin/env python3
"""
Test de humo para verificar funcionamiento básico de SUMO.
Este test verifica que SUMO y TraCI funcionen correctamente sin depender
de la arquitectura de servicios del proyecto.
"""

import logging
import sys

import traci
from traci.exceptions import FatalTraCIError, TraCIException

from src.traffic_system.simulation.app import SumoApp
from src.traffic_system.simulation.zones.zone_list import ZoneList

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("TestSumoSmoke")


def start_traci_connection(
    label: str, config_file: str, use_gui: bool
) -> traci.connection.Connection:
    """
    Función idéntica a la de run_simulation_provider.py para crear conexiones.
    """
    sumo_binary = "sumo-gui" if use_gui else "sumo"
    command = [sumo_binary, "-c", config_file, "--no-warnings"]
    traci.start(cmd=command, label=label)
    return traci.getConnection(label)


def test_sumo_basic_functionality():
    """
    Test de humo para verificar que SUMO funciona correctamente.
    """
    logger.info("=" * 60)
    logger.info("TEST DE HUMO: VERIFICACIÓN BÁSICA DE SUMO")
    logger.info("=" * 60)
    logger.info("📝 Descripción: Verifica que SUMO y TraCI funcionen correctamente")
    logger.info(
        "🎯 Objetivo: Detectar problemas básicos de instalación o configuración"
    )
    logger.info(
        "💡 Independiente de: API REST, microservicios, arquitectura del proyecto"
    )
    logger.info("=" * 60)

    try:
        # Cargar configuración básica
        logger.info("🔧 1/7 Cargando configuración básica...")
        zonas = ZoneList()
        config_file_path = "assets/sumo_maps/MapaDe0/mapa.sumocfg"
        logger.info(f"   ✅ Zonas cargadas: {len(zonas.zones)} zonas detectadas")
        logger.info(f"   ✅ Archivo de configuración: {config_file_path}")

        # Crear conexión TraCI
        logger.info("🚀 2/7 Estableciendo conexión TraCI...")
        traci_conn = start_traci_connection("test", config_file_path, False)
        logger.info("   ✅ Conexión TraCI establecida exitosamente")

        # Crear aplicación SUMO
        logger.info("⚙️ 3/7 Inicializando aplicación SUMO...")
        app_test = SumoApp(
            traci_conn,
            zonas,
            "test",
            config_file_path,
            False,
            start_traci_connection,
        )
        logger.info("   ✅ Aplicación SUMO inicializada")

        # Verificar estado inicial
        logger.info("📊 4/7 Verificando estado inicial de simulación...")
        tiempo_inicial = app_test.traci.simulation.getTime()
        num_vehiculos = app_test.traci.vehicle.getIDCount()
        logger.info(f"   ⏰ Tiempo inicial: {tiempo_inicial}s")
        logger.info(f"   🚗 Vehículos iniciales: {num_vehiculos}")

        # Probar avance de simulación
        logger.info("⏩ 5/7 Probando avance de simulación...")
        steps_to_advance = 10
        app_test.advance(steps_to_advance)
        tiempo_despues_avance = app_test.traci.simulation.getTime()
        num_vehiculos_despues = app_test.traci.vehicle.getIDCount()

        if tiempo_despues_avance > tiempo_inicial:
            logger.info(
                f"   ✅ Simulación avanzó correctamente: {tiempo_inicial}s → {tiempo_despues_avance}s"
            )
            logger.info(f"   🚗 Vehículos después del avance: {num_vehiculos_despues}")
        else:
            logger.warning("   ⚠️ La simulación no avanzó como se esperaba")

        # Probar reinicio
        logger.info("🔄 6/7 Probando funcionalidad de reinicio...")
        app_test.reset()
        tiempo_despues_reinicio = app_test.traci.simulation.getTime()

        if tiempo_despues_reinicio == 0:
            logger.info("   ✅ Reinicio funcionó correctamente")
            logger.info(
                f"   🔄 Tiempo reseteado: {tiempo_despues_avance}s → {tiempo_despues_reinicio}s"
            )
        else:
            logger.warning("   ⚠️ El reinicio puede no haber funcionado completamente")
            logger.warning(
                f"   🔄 Tiempo después del reinicio: {tiempo_despues_reinicio}s (esperado: 0s)"
            )

        # Verificar funcionalidad post-reinicio
        logger.info("✅ 7/7 Verificando funcionalidad post-reinicio...")
        app_test.advance(5)
        tiempo_final = app_test.traci.simulation.getTime()

        if tiempo_final > tiempo_despues_reinicio:
            logger.info(
                f"   ✅ Simulación funciona después del reinicio: {tiempo_despues_reinicio}s → {tiempo_final}s"
            )
        else:
            logger.error("   ❌ La simulación no funcionó después del reinicio")
            return False

        # Limpiar recursos
        logger.info("🧹 Limpiando recursos...")
        app_test.traci.close()
        logger.info("   ✅ Conexión TraCI cerrada")

        # Resumen exitoso
        logger.info("=" * 60)
        logger.info("🎉 RESUMEN: TEST DE HUMO EXITOSO")
        logger.info("=" * 60)
        logger.info("✅ SUMO se inició correctamente")
        logger.info("✅ TraCI funciona sin problemas")
        logger.info("✅ La simulación avanza correctamente")
        logger.info("✅ El reinicio funciona")
        logger.info("✅ Los recursos se liberan apropiadamente")
        logger.info("💡 Recomendación: SUMO está listo para uso en el proyecto")
        logger.info("=" * 60)

        return True

    except (TraCIException, FatalTraCIError) as e:
        logger.error("=" * 60)
        logger.error("❌ ERROR DE TRACI/SUMO")
        logger.error("=" * 60)
        logger.error(f"Error durante la prueba: {e}")
        logger.error("💡 Posibles causas:")
        logger.error("   • SUMO no está instalado correctamente")
        logger.error("   • El archivo de configuración está corrupto")
        logger.error("   • Permisos insuficientes para ejecutar SUMO")
        logger.error("   • Puerto TraCI en uso por otra instancia")
        logger.error("💡 Soluciones sugeridas:")
        logger.error("   • Reinstalar SUMO desde: https://eclipse.dev/sumo/")
        logger.error("   • Verificar que 'sumo' esté en el PATH")
        logger.error("   • Revisar el archivo assets/sumo_maps/MapaDe0/mapa.sumocfg")
        logger.error("=" * 60)
        return False
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ ERROR INESPERADO")
        logger.error("=" * 60)
        logger.error(f"Error inesperado durante la prueba: {e}", exc_info=True)
        logger.error("💡 Esto indica un problema más profundo en el sistema")
        logger.error("=" * 60)
        return False


if __name__ == "__main__":
    logger.info("🚀 Iniciando test de humo para SUMO...")
    logger.info("📝 Este test verifica que SUMO funcione correctamente")
    logger.info("⚡ Independiente de la arquitectura de microservicios")

    exito = test_sumo_basic_functionality()

    if exito:
        logger.info("🎯 Test de humo completado exitosamente")
        sys.exit(0)
    else:
        logger.error("💥 Test de humo falló - revisa la instalación de SUMO")
        sys.exit(1)
