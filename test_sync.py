#!/usr/bin/env python3
"""
Script de prueba para verificar la sincronización entre simulaciones.
Este script hace llamadas a la API para probar que las simulaciones se mantengan sincronizadas.
"""

import logging
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("TestSync")

API_BASE_URL = "http://localhost:5000"


def test_simulation_sync():
    """Prueba la sincronización de las simulaciones."""
    logger.info("🧪 Iniciando prueba de sincronización...")

    # Verificar que la API esté disponible
    try:
        response = requests.get(f"{API_BASE_URL}/simulacion")
        if response.status_code != 200:
            logger.error("❌ La API no está disponible")
            return False
    except requests.ConnectionError:
        logger.error(
            "❌ No se puede conectar a la API. ¿Está ejecutándose el servidor?"
        )
        return False

    # Verificar sincronización inicial
    try:
        response = requests.get(f"{API_BASE_URL}/sincronizacion")
        if response.status_code == 200:
            sync_data = response.json()
            logger.info(f"📊 Sincronización inicial: {sync_data}")
        else:
            logger.warning("⚠️  No hay simulación de comparación activa")
    except Exception as e:
        logger.error(f"❌ Error verificando sincronización inicial: {e}")

    # Realizar varias iteraciones de avance
    for i in range(5):
        logger.info(f"🔄 Iteración {i+1}/5: Avanzando 15 pasos...")

        try:
            # Avanzar simulación
            response = requests.put(f"{API_BASE_URL}/avanzar?steps=15")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Avance exitoso: {data}")

                # Verificar sincronización después del avance
                if not data.get("done", False):
                    time.sleep(1)  # Pequeña pausa
                    sync_response = requests.get(f"{API_BASE_URL}/sincronizacion")
                    if sync_response.status_code == 200:
                        sync_data = sync_response.json()
                        sync_status = "✅" if sync_data["sincronizado"] else "❌"
                        logger.info(
                            f"{sync_status} Sincronización: S1={sync_data['tiempo_s1']:.1f}s, S2={sync_data['tiempo_s2']:.1f}s, diff={sync_data['diferencia']:.1f}s"
                        )
                    else:
                        logger.info(
                            "ℹ️  No hay simulación de comparación para verificar"
                        )
                else:
                    logger.info("🏁 Simulación terminada")
                    break
            else:
                logger.error(f"❌ Error avanzando simulación: {response.status_code}")
                break

        except Exception as e:
            logger.error(f"❌ Error en iteración {i+1}: {e}")
            break

        time.sleep(2)  # Pausa entre iteraciones

    logger.info("🧪 Prueba de sincronización completada")
    return True


def test_endpoints():
    """Prueba todos los endpoints de la API."""
    logger.info("🧪 Probando endpoints de la API...")

    endpoints = [
        ("/simulacion", "GET"),
        ("/espera", "GET"),
        ("/semaforo", "GET"),
        ("/reporte", "GET"),
        ("/sincronizacion", "GET"),
    ]

    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}")

            logger.info(f"📡 {method} {endpoint}: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if endpoint == "/sincronizacion" and "sincronizado" in data:
                    sync_status = "✅" if data["sincronizado"] else "❌"
                    logger.info(
                        f"   {sync_status} Sincronizado: {data['sincronizado']}"
                    )
                elif endpoint == "/espera" and "tiempo_espera_total" in data:
                    logger.info(
                        f"   ⏱️  Tiempo espera total: {data['tiempo_espera_total']:.2f}s"
                    )
                elif endpoint == "/simulacion" and "simulacion" in data:
                    status = "✅" if data["simulacion"] else "❌"
                    logger.info(f"   {status} Simulación activa: {data['simulacion']}")

        except Exception as e:
            logger.error(f"❌ Error probando {endpoint}: {e}")


if __name__ == "__main__":
    logger.info("🚀 Iniciando script de prueba de sincronización")
    logger.info(
        "📝 Asegúrate de que el servidor esté ejecutándose con 'python run_simulation_provider.py'"
    )

    # Pequeña pausa para dar tiempo al usuario
    time.sleep(3)

    # Probar endpoints básicos
    test_endpoints()

    print("\n" + "=" * 50 + "\n")

    # Probar sincronización
    test_simulation_sync()

    logger.info("🎯 Script de prueba completado")
