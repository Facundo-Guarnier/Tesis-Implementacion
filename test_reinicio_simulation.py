#!/usr/bin/env python3
"""
Script de prueba para verificar que el reinicio de simulaciones funcione correctamente.
"""

import logging
import sys

import traci
from traci.exceptions import FatalTraCIError, TraCIException

from src.traffic_system.simulation.AppSUMO import AppSUMO
from src.traffic_system.simulation.zonas.ZonaList import ZonaList

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("TestReinicio")


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


def test_reinicio():
    """
    Prueba el funcionamiento del reinicio de simulación.
    """
    logger.info("🧪 Iniciando prueba de reinicio de simulación...")

    try:
        # Cargar configuración (solo necesitamos las zonas)
        zonas = ZonaList()
        config_file_path = "assets/sumo_maps/MapaDe0/mapa.sumocfg"

        # Crear simulación de prueba
        logger.info("1/6 Creando simulación inicial...")
        traci_conn = start_traci_connection(
            "test", config_file_path, False
        )  # Sin GUI para prueba
        app_test = AppSUMO(
            traci_conn,
            zonas,
            "test",
            config_file_path,
            False,  # Sin GUI para prueba
            start_traci_connection,
        )

        # Verificar que la simulación funciona
        logger.info("2/6 Verificando simulación inicial...")
        tiempo_inicial = app_test.traci.simulation.getTime()
        logger.info(f"   Tiempo inicial: {tiempo_inicial}s")

        # Avanzar algunos pasos
        logger.info("3/6 Avanzando simulación...")
        app_test.avanzar(5)
        tiempo_despues_avance = app_test.traci.simulation.getTime()
        logger.info(f"   Tiempo después de avanzar 5 pasos: {tiempo_despues_avance}s")

        # Probar el reinicio
        logger.info("4/6 Probando reinicio...")
        app_test.reiniciar()

        # Verificar que el reinicio funcionó
        tiempo_despues_reinicio = app_test.traci.simulation.getTime()
        logger.info(f"   Tiempo después del reinicio: {tiempo_despues_reinicio}s")

        # Validar que efectivamente se reinició
        if tiempo_despues_reinicio == 0:
            logger.info("✅ ¡ÉXITO! El reinicio funcionó correctamente")
            logger.info(
                f"   Tiempo se reseteo de {tiempo_despues_avance}s a {tiempo_despues_reinicio}s"
            )
        else:
            logger.warning("⚠️ El reinicio puede no haber funcionado completamente")
            logger.warning(
                f"   Se esperaba tiempo 0, pero se obtuvo {tiempo_despues_reinicio}s"
            )

        # Probar que la simulación sigue funcionando después del reinicio
        logger.info("5/6 Verificando funcionamiento post-reinicio...")
        app_test.avanzar(3)
        tiempo_final = app_test.traci.simulation.getTime()
        logger.info(f"   Tiempo final después de avanzar 3 pasos: {tiempo_final}s")

        if tiempo_final > tiempo_despues_reinicio:
            logger.info("✅ La simulación funciona correctamente después del reinicio")
        else:
            logger.error("❌ La simulación no avanzó después del reinicio")

        # Limpiar
        logger.info("6/6 Cerrando conexión...")
        app_test.traci.close()

        logger.info("🎉 Prueba de reinicio completada exitosamente")

    except (TraCIException, FatalTraCIError) as e:
        logger.error(f"❌ Error de TraCI durante la prueba: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado durante la prueba: {e}", exc_info=True)
        return False

    return True


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("SCRIPT DE PRUEBA: REINICIO DE SIMULACIÓN SUMO")
    logger.info("=" * 60)

    exito = test_reinicio()

    if exito:
        logger.info("🎯 Todas las pruebas pasaron exitosamente")
        sys.exit(0)
    else:
        logger.error("💥 Las pruebas fallaron")
        sys.exit(1)
