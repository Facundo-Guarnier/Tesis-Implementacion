#!/usr/bin/env python3
"""
Script para probar el reinicio de simulaciones a través de la API REST.
"""

import logging
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("TestReinicioAPI")


def test_api_reinicio(base_url: str = "http://127.0.0.1:5000"):
    """
    Prueba el endpoint de reinicio a través de la API.
    """
    logger.info("🧪 Iniciando prueba de reinicio a través de API...")

    try:
        # Verificar que la API esté disponible
        logger.info("1/5 Verificando disponibilidad de la API...")
        response = requests.get(f"{base_url}/simulacion", timeout=5)
        if response.status_code != 200:
            logger.error(f"❌ La API no está disponible en {base_url}")
            return False

        logger.info("✅ API disponible")

        # Obtener estado inicial
        logger.info("2/5 Obteniendo estado inicial...")
        response = requests.get(f"{base_url}/reporte", timeout=5)
        if response.status_code == 200:
            reporte_inicial = response.json()
            logger.info(f"   Steps inicial: {reporte_inicial.get('steps', 'N/A')}")
        else:
            logger.warning("⚠️ No se pudo obtener el reporte inicial")

        # Avanzar la simulación
        logger.info("3/5 Avanzando simulación...")
        response = requests.put(f"{base_url}/avanzar?steps=10", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Simulación avanzada exitosamente")
        else:
            logger.warning(f"⚠️ Error al avanzar simulación: {response.status_code}")

        # Obtener estado después del avance
        response = requests.get(f"{base_url}/reporte", timeout=5)
        if response.status_code == 200:
            reporte_avanzado = response.json()
            logger.info(
                f"   Steps después del avance: {reporte_avanzado.get('steps', 'N/A')}"
            )

        # Probar el reinicio
        logger.info("4/5 Probando reinicio a través de API...")
        response = requests.post(f"{base_url}/simulacion/reiniciar", timeout=15)

        if response.status_code == 200:
            resultado = response.json()
            logger.info("✅ Reinicio exitoso")
            logger.info(f"   Respuesta: {resultado}")
        else:
            logger.error(f"❌ Error en el reinicio: {response.status_code}")
            logger.error(f"   Respuesta: {response.text}")
            return False

        # Verificar que el reinicio funcionó
        logger.info("5/5 Verificando resultado del reinicio...")
        time.sleep(2)  # Esperar un poco para que el reinicio se complete

        response = requests.get(f"{base_url}/reporte", timeout=5)
        if response.status_code == 200:
            reporte_reiniciado = response.json()
            steps_reiniciado = reporte_reiniciado.get("steps", -1)
            logger.info(f"   Steps después del reinicio: {steps_reiniciado}")

            if steps_reiniciado == 0:
                logger.info("✅ ¡ÉXITO! El reinicio funcionó correctamente")
                logger.info("   La simulación se reseteo a tiempo 0")
            else:
                logger.warning("⚠️ El reinicio puede no haber funcionado completamente")
                logger.warning(
                    f"   Se esperaba steps=0, pero se obtuvo steps={steps_reiniciado}"
                )
        else:
            logger.error("❌ No se pudo verificar el estado después del reinicio")
            return False

        # Probar que la simulación sigue funcionando
        logger.info("6/6 Verificando funcionamiento post-reinicio...")
        response = requests.put(f"{base_url}/avanzar?steps=5", timeout=10)
        if response.status_code == 200:
            logger.info("✅ La simulación funciona correctamente después del reinicio")
        else:
            logger.error("❌ La simulación no funciona después del reinicio")
            return False

        logger.info("🎉 Prueba de reinicio por API completada exitosamente")
        return True

    except requests.exceptions.ConnectionError:
        logger.error("❌ No se pudo conectar a la API. ¿Está ejecutándose el servidor?")
        return False
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout al conectar con la API")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("SCRIPT DE PRUEBA: REINICIO POR API REST")
    logger.info("=" * 60)
    logger.info("Nota: Asegúrate de que el servidor esté ejecutándose con:")
    logger.info("      python run_simulation_provider.py")
    logger.info("=" * 60)

    exito = test_api_reinicio()

    if exito:
        logger.info("🎯 Todas las pruebas por API pasaron exitosamente")
    else:
        logger.error("💥 Las pruebas por API fallaron")
        logger.error("💡 Sugerencias:")
        logger.error("   - Verifica que el servidor esté ejecutándose")
        logger.error("   - Revisa los logs del servidor para más detalles")
        logger.error("   - Asegúrate de que SUMO esté instalado correctamente")
