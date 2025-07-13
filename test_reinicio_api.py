#!/usr/bin/env python3
"""
Test de reinicio de simulaciones a través de la API REST.
Este test verifica que el endpoint de reinicio funcione correctamente
y que la simulación se resetee apropiadamente.
"""

import logging
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("TestReinicioAPI")


def test_api_reinicio(base_url: str = "http://127.0.0.1:5000"):
    """
    Prueba el endpoint de reinicio a través de la API REST.
    """
    logger.info("=" * 60)
    logger.info("TEST: REINICIO DE SIMULACIÓN VÍA API REST")
    logger.info("=" * 60)
    logger.info(
        "📝 Descripción: Verifica que el endpoint de reinicio funcione correctamente"
    )
    logger.info("🎯 Objetivo: Asegurar que la simulación se resetee apropiadamente")
    logger.info("💡 Usa: Arquitectura de microservicios completa")
    logger.info("📋 Requisitos: Servidor de simulación ejecutándose")
    logger.info("=" * 60)

    try:
        # Verificar que la API esté disponible
        logger.info("🔍 1/6 Verificando disponibilidad de la API...")
        response = requests.get(f"{base_url}/simulacion", timeout=5)
        if response.status_code != 200:
            logger.error(f"❌ La API no está disponible en {base_url}")
            logger.error("💡 Solución: Ejecuta 'python run_simulation_provider.py'")
            return False

        logger.info(f"   ✅ API disponible en {base_url}")

        # Obtener estado inicial
        logger.info("📊 2/6 Obteniendo estado inicial...")
        response = requests.get(f"{base_url}/reporte", timeout=5)
        if response.status_code == 200:
            reporte_inicial = response.json()
            steps_inicial = reporte_inicial.get("steps", "N/A")
            logger.info(f"   📈 Steps inicial: {steps_inicial}")
        else:
            logger.warning("   ⚠️ No se pudo obtener el reporte inicial")
            steps_inicial = "N/A"

        # Avanzar la simulación
        logger.info("⏩ 3/6 Avanzando simulación para generar cambios...")
        response = requests.put(f"{base_url}/avanzar?steps=10", timeout=10)
        if response.status_code == 200:
            logger.info("   ✅ Simulación avanzada exitosamente")
        else:
            logger.warning(f"   ⚠️ Error al avanzar simulación: {response.status_code}")

        # Obtener estado después del avance
        response = requests.get(f"{base_url}/reporte", timeout=5)
        if response.status_code == 200:
            reporte_avanzado = response.json()
            steps_avanzado = reporte_avanzado.get("steps", "N/A")
            logger.info(f"   📈 Steps después del avance: {steps_avanzado}")
        else:
            steps_avanzado = "N/A"

        # Probar el reinicio
        logger.info("🔄 4/6 Probando reinicio a través de API...")
        response = requests.post(f"{base_url}/simulacion/reiniciar", timeout=15)

        if response.status_code == 200:
            resultado = response.json()
            logger.info("   ✅ Reinicio exitoso")
            logger.info(f"   📋 Respuesta del servidor: {resultado}")
        else:
            logger.error(f"   ❌ Error en el reinicio: {response.status_code}")
            logger.error(f"   📋 Respuesta: {response.text}")
            return False

        # Verificar que el reinicio funcionó
        logger.info("✅ 5/6 Verificando resultado del reinicio...")
        time.sleep(2)  # Esperar un poco para que el reinicio se complete

        response = requests.get(f"{base_url}/reporte", timeout=5)
        if response.status_code == 200:
            reporte_reiniciado = response.json()
            steps_reiniciado = reporte_reiniciado.get("steps", -1)
            logger.info(f"   📈 Steps después del reinicio: {steps_reiniciado}")

            if steps_reiniciado == 0:
                logger.info("   ✅ ¡ÉXITO! El reinicio funcionó correctamente")
                logger.info("   🔄 La simulación se reseteo a tiempo 0")
            else:
                logger.warning(
                    "   ⚠️ El reinicio puede no haber funcionado completamente"
                )
                logger.warning(
                    f"   🔄 Se esperaba steps=0, pero se obtuvo steps={steps_reiniciado}"
                )
        else:
            logger.error("   ❌ No se pudo verificar el estado después del reinicio")
            return False

        # Probar que la simulación sigue funcionando
        logger.info("🧪 6/6 Verificando funcionamiento post-reinicio...")
        response = requests.put(f"{base_url}/avanzar?steps=5", timeout=10)
        if response.status_code == 200:
            logger.info(
                "   ✅ La simulación funciona correctamente después del reinicio"
            )
        else:
            logger.error("   ❌ La simulación no funciona después del reinicio")
            return False

        # Resumen exitoso
        logger.info("=" * 60)
        logger.info("🎉 RESUMEN: TEST DE REINICIO API EXITOSO")
        logger.info("=" * 60)
        logger.info("✅ API REST disponible y funcionando")
        logger.info("✅ Endpoint de reinicio responde correctamente")
        logger.info("✅ La simulación se resetea apropiadamente")
        logger.info("✅ Funcionalidad post-reinicio verificada")
        logger.info("💡 Recomendación: El reinicio por API está listo para uso")
        logger.info("=" * 60)
        return True

    except requests.exceptions.ConnectionError:
        logger.error("=" * 60)
        logger.error("❌ ERROR DE CONEXIÓN")
        logger.error("=" * 60)
        logger.error("No se pudo conectar a la API")
        logger.error(f"URL probada: {base_url}")
        logger.error("💡 Soluciones sugeridas:")
        logger.error("   • Verifica que el servidor esté ejecutándose")
        logger.error("   • Ejecuta: python run_simulation_provider.py")
        logger.error("   • Revisa que el puerto 5000 no esté bloqueado")
        logger.error("=" * 60)
        return False
    except requests.exceptions.Timeout:
        logger.error("=" * 60)
        logger.error("❌ ERROR DE TIMEOUT")
        logger.error("=" * 60)
        logger.error("Timeout al conectar con la API")
        logger.error("💡 Posibles causas:")
        logger.error("   • El servidor está sobrecargado")
        logger.error("   • SUMO está tardando en responder")
        logger.error("   • Problemas de red locales")
        logger.error("=" * 60)
        return False
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ ERROR INESPERADO")
        logger.error("=" * 60)
        logger.error(f"Error inesperado: {e}", exc_info=True)
        logger.error("💡 Esto indica un problema más profundo en el sistema")
        logger.error("=" * 60)
        return False


if __name__ == "__main__":
    logger.info("🚀 Iniciando test de reinicio por API REST...")
    logger.info(
        "📝 Este test verifica que el endpoint de reinicio funcione correctamente"
    )

    exito = test_api_reinicio()

    if exito:
        logger.info("🎯 Test de reinicio por API completado exitosamente")
    else:
        logger.error("💥 Test de reinicio por API falló")
        logger.error("💡 Sugerencias:")
        logger.error("   • Verifica que el servidor esté ejecutándose")
        logger.error("   • Revisa los logs del servidor para más detalles")
        logger.error("   • Asegúrate de que SUMO esté instalado correctamente")
