#!/usr/bin/env python3
"""
Script de prueba para verificar que los cambios de semáforos no rompan la sincronización.
Este script simula el comportamiento de la aplicación de decisiones.
"""

import logging
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("TestSemaforoSync")

API_BASE_URL = "http://localhost:5000"


def test_semaforo_sync():
    """Prueba que los cambios de semáforos mantengan la sincronización."""
    logger.info("🧪 Iniciando prueba de sincronización con cambios de semáforos...")

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
    def verificar_sync(momento, spacing=""):
        try:
            response = requests.get(f"{API_BASE_URL}/sincronizacion")
            if response.status_code == 200:
                sync_data = response.json()
                sync_status = "✅" if sync_data["sincronizado"] else "❌"
                fase_info = f" ({sync_data.get('fase', 'normal')})"
                logger.info(
                    f"{spacing}{sync_status} {momento}{fase_info}: S1={sync_data['tiempo_s1']:.1f}s, "
                    f"S2={sync_data['tiempo_s2']:.1f}s, diff={sync_data['diferencia']:.1f}s "
                    f"(max: {sync_data['max_diferencia_permitida']:.1f}s)"
                )
                return sync_data["sincronizado"]
            else:
                logger.warning("⚠️  No hay simulación de comparación activa")
                return True
        except Exception as e:
            logger.error(f"❌ Error verificando sincronización: {e}")
            return False

    # Verificar sincronización inicial
    verificar_sync("Sincronización inicial")

    # Hacer algunos avances normales primero
    logger.info("🔄 Realizando avances normales...")
    for i in range(3):
        logger.info(f"   Avance normal {i+1}/3: 15 pasos")
        response = requests.put(f"{API_BASE_URL}/avanzar?steps=15")
        if response.status_code == 200:
            data = response.json()
            if data.get("done", False):
                logger.info("🏁 Simulación terminada durante avances normales")
                return True
        else:
            logger.error(f"❌ Error en avance normal: {response.status_code}")
            return False
        time.sleep(1)

    verificar_sync("Después de avances normales")

    # Definir algunos cambios de semáforos de prueba
    cambios_semaforos = [
        {
            "descripcion": "Cambio individual - Semáforo 3",
            "endpoint": "/semaforo/3",
            "method": "PUT",
            "params": {"estado": "rrrrGGGGGGrr"},
        },
        {
            "descripcion": "Cambio individual - Semáforo 4",
            "endpoint": "/semaforo/4",
            "method": "PUT",
            "params": {"estado": "rrrGGGGrrr"},
        },
        {
            "descripcion": "Cambio múltiple - Semáforos 1,2",
            "endpoint": "/semaforo",
            "method": "PUT",
            "json": {
                "data": [
                    {"id": "1", "estado": "rrrrrrGGgGG"},  # GGGGGGrrrrr o "rrrrrrGGgGG"
                    {
                        "id": "2",
                        "estado": "GrrrGGGGrrrr",  # GgGGrrrrGgGg o GrrrGGGGrrrr
                    },
                ]
            },
        },
        {
            "descripcion": "Cambio múltiple - Semáforos 1,2,3,4",
            "endpoint": "/semaforo",
            "method": "PUT",
            "json": {
                "data": [
                    {"id": "1", "estado": "GGGGGGrrrrr"},  # GGGGGGrrrrr o "rrrrrrGGgGG"
                    {
                        "id": "2",
                        "estado": "GgGGrrrrGgGg",  # GgGGrrrrGgGg o GrrrGGGGrrrr
                    },
                    {
                        "id": "3",
                        "estado": "GgGgGgGGrrrr",  # rrrrGGGGGGrr o GgGgGgGGrrrr
                    },
                    {"id": "4", "estado": "GGGrrrrGGg"},  # rrrGGGGrrr o GGGrrrrGGg
                ]
            },
        },
    ]

    # Probar cada cambio de semáforo
    for i, cambio in enumerate(cambios_semaforos, 1):
        logger.info(f"🚦 Prueba {i}/{len(cambios_semaforos)}: {cambio['descripcion']}")

        try:
            # Realizar el cambio de semáforo
            if cambio["method"] == "PUT":
                if "params" in cambio:
                    response = requests.put(
                        f"{API_BASE_URL}{cambio['endpoint']}", params=cambio["params"]
                    )
                elif "json" in cambio:
                    response = requests.put(
                        f"{API_BASE_URL}{cambio['endpoint']}", json=cambio["json"]
                    )

            if response.status_code == 200:
                logger.info("   ✅Cambio aplicado exitosamente")

                # Pequeña pausa para que se procese
                time.sleep(0.5)

                # Verificar sincronización después del cambio
                if verificar_sync(f"Después de {cambio['descripcion']}", spacing="   "):
                    logger.info("   ✅ Sincronización mantenida")
                else:
                    logger.error(
                        f"   ❌ Sincronización perdida después de {cambio['descripcion']}"
                    )
                    return False

            else:
                logger.error(
                    f"   ❌ Error aplicando cambio: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"   ❌ Error en prueba de semáforo: {e}")
            return False

        # Pausa entre cambios
        time.sleep(2)

    # Hacer algunos avances finales para verificar que todo sigue bien
    logger.info("🔄 Realizando avances finales...")
    for i in range(2):
        logger.info(f"   Avance final {i+1}/2: 15 pasos")
        response = requests.put(f"{API_BASE_URL}/avanzar?steps=15")
        if response.status_code == 200:
            data = response.json()
            if data.get("done", False):
                logger.info("🏁 Simulación terminada durante avances finales")
                break
        time.sleep(1)

    verificar_sync("Sincronización final")

    logger.info("🎯 Prueba de sincronización con semáforos completada exitosamente")
    return True


if __name__ == "__main__":
    logger.info("🚀 Iniciando script de prueba de sincronización con semáforos")
    logger.info(
        "📝 Asegúrate de que el servidor esté ejecutándose con modo comparación habilitado"
    )

    # Pequeña pausa para dar tiempo al usuario
    time.sleep(3)

    success = test_semaforo_sync()

    if success:
        logger.info("🎉 ¡Todas las pruebas pasaron exitosamente!")
    else:
        logger.error("💥 Algunas pruebas fallaron")
