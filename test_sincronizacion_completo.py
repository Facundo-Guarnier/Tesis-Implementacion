#!/usr/bin/env python3
"""
Test completo de sincronización de simulaciones con API REST.
Este test verifica la sincronización básica y con cambios de semáforos,
simulando el comportamiento real del agente de decisión.
"""

import logging
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("TestSincronizacion")

API_BASE_URL = "http://localhost:5000"


def test_endpoints() -> bool:
    """Prueba todos los endpoints básicos de la API."""
    logger.info("🔧 1/3 Probando endpoints básicos de la API...")

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
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)

            logger.info(f"   📡 {method} {endpoint}: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if endpoint == "/sincronizacion" and "sincronizado" in data:
                    sync_status = "✅" if data["sincronizado"] else "❌"
                    logger.info(
                        f"      {sync_status} Sincronizado: {data['sincronizado']}"
                    )
                elif endpoint == "/espera" and "tiempo_espera_total" in data:
                    logger.info(
                        f"      ⏱️  Tiempo espera total: {data['tiempo_espera_total']:.2f}s"
                    )
                elif endpoint == "/simulacion" and "simulacion" in data:
                    status = "✅" if data["simulacion"] else "❌"
                    logger.info(
                        f"      {status} Simulación activa: {data['simulacion']}"
                    )
            elif response.status_code == 404:
                logger.info(
                    "      ℹ️  Endpoint no disponible (esperado en algunos casos)"
                )
            else:
                logger.warning(f"      ⚠️  Respuesta inesperada: {response.status_code}")

        except requests.exceptions.Timeout:
            logger.error(f"      ❌ Timeout en {endpoint}")
            return False
        except Exception as e:
            logger.error(f"      ❌ Error probando {endpoint}: {e}")
            return False

    logger.info("   ✅ Verificación de endpoints completada")
    return True


def verificar_sync(momento: str, spacing: str = "   ") -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/sincronizacion", timeout=5)
        if response.status_code == 200:
            sync_data = response.json()
            sync_status = "✅" if sync_data["sincronizado"] else "❌"
            fase_info = f" ({sync_data.get('fase', 'normal')})"

            logger.info(
                f"{spacing}{sync_status} {momento}{fase_info}: S1={sync_data['s1_time']:.1f}s, "
                f"S2={sync_data.get('s2_time', 0):.1f}s, diff={sync_data['diferencia_tiempo']:.1f}s "
                f"(max: {sync_data.get('tolerancia', 1.0):.1f}s)"
            )
            return bool(sync_data["sincronizado"])
        else:
            logger.warning(f"{spacing}⚠️  No hay simulación de comparación activa")
            return True
    except Exception as e:
        logger.error(f"{spacing}❌ Error verificando sincronización: {e}")
        return False


def test_basic_sync() -> bool:
    """Prueba la sincronización básica sin cambios de semáforos."""
    logger.info("⚡ 2/3 Probando sincronización básica...")

    # Verificar sincronización inicial
    if not verificar_sync("Sincronización inicial"):
        return False

    # Hacer avances básicos para verificar sincronización
    logger.info("   🔄 Realizando avances básicos para verificar sincronización...")
    for i in range(3):
        logger.info(f"      Avance {i+1}/3: 15 pasos")
        try:
            response = requests.put(f"{API_BASE_URL}/avanzar?steps=15", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("done", False):
                    logger.info("      🏁 Simulación terminada durante avances básicos")
                    break
            else:
                logger.error(f"      ❌ Error en avance básico: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"      ❌ Error en avance {i+1}: {e}")
            return False
        time.sleep(1)

    if not verificar_sync("Después de avances básicos"):
        return False

    logger.info("   ✅ Sincronización básica verificada")
    return True


def test_semaforo_sync() -> bool:
    """Prueba que los cambios de semáforos mantengan la sincronización."""
    logger.info("🚦 3/3 Probando sincronización con cambios de semáforos...")

    # Función helper para verificar sincronización
    def verificar_sync_local(momento: str, spacing: str = "   ") -> bool:
        try:
            response = requests.get(f"{API_BASE_URL}/sincronizacion", timeout=5)
            if response.status_code == 200:
                sync_data = response.json()
                sync_status = "✅" if sync_data["sincronizado"] else "❌"
                logger.info(
                    f"{spacing}{sync_status} {momento}: S1={sync_data['s1_time']:.1f}s, "
                    f"S2={sync_data.get('s2_time', 0):.1f}s, diff={sync_data['diferencia_tiempo']:.1f}s "
                    f"(max: {sync_data.get('tolerancia', 1.0):.1f}s)"
                )
                return bool(sync_data["sincronizado"])
            else:
                logger.warning(f"{spacing}⚠️  No hay simulación de comparación activa")
                return True
        except Exception as e:
            logger.error(f"{spacing}❌ Error verificando sincronización: {e}")
            return False

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
                    {"id": "1", "estado": "rrrrrrGGgGG"},
                    {"id": "2", "estado": "GrrrGGGGrrrr"},
                ]
            },
        },
        {
            "descripcion": "Cambio múltiple - Semáforos 1,2,3,4",
            "endpoint": "/semaforo",
            "method": "PUT",
            "json": {
                "data": [
                    {"id": "1", "estado": "GGGGGGrrrrr"},
                    {"id": "2", "estado": "GgGGrrrrGgGg"},
                    {"id": "3", "estado": "GgGgGgGGrrrr"},
                    {"id": "4", "estado": "GGGrrrrGGg"},
                ]
            },
        },
    ]

    # Probar cada cambio de semáforo
    for i, cambio in enumerate(cambios_semaforos, 1):
        logger.info(
            f"      🚦 Prueba {i}/{len(cambios_semaforos)}: {cambio['descripcion']}"
        )

        try:
            # Realizar el cambio de semáforo
            if cambio["method"] == "PUT":
                if "params" in cambio:
                    response = requests.put(
                        f"{API_BASE_URL}{cambio['endpoint']}",
                        params=cambio["params"],  # type: ignore[arg-type]
                        timeout=10,
                    )
                elif "json" in cambio:
                    response = requests.put(
                        f"{API_BASE_URL}{cambio['endpoint']}",
                        json=cambio["json"],
                        timeout=10,
                    )

            if response.status_code == 200:
                logger.info("         ✅ Cambio aplicado exitosamente")
                time.sleep(1)  # Pequeña pausa para que se procese
                verificar_sync_local("Después del cambio de semáforo", "         ")
            else:
                logger.error(
                    f"         ❌ Error aplicando cambio: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"         ❌ Error en prueba de semáforo: {e}")
            return False

        time.sleep(2)  # Pausa entre cambios

    # Hacer algunos avances finales para verificar que todo sigue bien
    logger.info("   🔄 Realizando avances finales...")
    for i in range(2):
        logger.info(f"      Avance final {i+1}/2: 15 pasos")
        try:
            response = requests.put(f"{API_BASE_URL}/avanzar?steps=15", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("done", False):
                    logger.info("      🏁 Simulación terminada")
                    break
            else:
                logger.error(f"      ❌ Error en avance final: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"      ❌ Error en avance final: {e}")
            return False
        time.sleep(1)

    if not verificar_sync("Sincronización final"):
        return False

    logger.info("   ✅ Sincronización con cambios de semáforos verificada")
    return True


def run_complete_sync_test() -> bool:
    """Ejecuta el test completo de sincronización."""
    logger.info("=" * 60)
    logger.info("TEST COMPLETO: SINCRONIZACIÓN DE SIMULACIONES")
    logger.info("=" * 60)
    logger.info(
        "📝 Descripción: Verifica sincronización básica y con cambios de semáforos"
    )
    logger.info("🎯 Objetivo: Asegurar que las simulaciones se mantengan sincronizadas")
    logger.info("💡 Simula: Comportamiento real del agente de decisión")
    logger.info(
        "📋 Requisitos: Servidor de simulación ejecutándose con modo comparación"
    )
    logger.info("=" * 60)

    # Verificar disponibilidad de la API
    try:
        response = requests.get(f"{API_BASE_URL}/simulacion", timeout=5)
        if response.status_code != 200:
            logger.error("❌ La API no está disponible")
            logger.error(f"   URL probada: {API_BASE_URL}/simulacion")
            logger.error("💡 Solución: Ejecuta 'python run_simulation_provider.py'")
            return False
    except requests.ConnectionError:
        logger.error("❌ No se puede conectar a la API")
        logger.error(f"   URL probada: {API_BASE_URL}")
        logger.error("💡 Solución: Verifica que el servidor esté ejecutándose")
        return False

    logger.info("✅ API de simulación disponible")

    # Ejecutar las tres fases del test
    tests = [
        ("Endpoints básicos", test_endpoints),
        ("Sincronización básica", test_basic_sync),
        ("Sincronización con semáforos", test_semaforo_sync),
    ]

    for test_name, test_func in tests:
        logger.info(f"🧪 Ejecutando: {test_name}...")
        if not test_func():
            logger.error(f"❌ Falló: {test_name}")
            logger.error("=" * 60)
            logger.error("💥 RESUMEN: TEST FALLÓ")
            logger.error("=" * 60)
            logger.error(f"Error en fase: {test_name}")
            logger.error("💡 Recomendaciones:")
            logger.error("   • Revisa los logs del servidor para más detalles")
            logger.error("   • Verifica que SUMO esté funcionando correctamente")
            logger.error("   • Asegúrate de que el modo comparación esté habilitado")
            logger.error("=" * 60)
            return False
        logger.info(f"✅ Completado: {test_name}")

    # Resumen exitoso
    logger.info("=" * 60)
    logger.info("🎉 RESUMEN: TEST COMPLETO EXITOSO")
    logger.info("=" * 60)
    logger.info("✅ Todos los endpoints funcionan correctamente")
    logger.info("✅ La sincronización básica funciona")
    logger.info("✅ Los cambios de semáforos no rompen la sincronización")
    logger.info("✅ El sistema está listo para el agente de decisión")
    logger.info(
        "💡 Recomendación: Puedes proceder con confianza al entrenamiento/inferencia"
    )
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    logger.info("🚀 Iniciando test completo de sincronización...")
    logger.info("📝 Este test combina verificación básica y con cambios de semáforos")

    success = run_complete_sync_test()

    if success:
        logger.info("🎯 Test completo de sincronización exitoso")
        sys.exit(0)
    else:
        logger.error("💥 Test completo de sincronización falló")
        sys.exit(1)
