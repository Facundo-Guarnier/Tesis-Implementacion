import logging
import os
import sqlite3
import time

import numpy as np

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.simulation.app import SumoApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")
logger = logging.getLogger("ComparisonLogger")


class ComparisonLogger:
    """
    Una clase pasiva para registrar métricas comparativas entre dos simulaciones.
    No ejecuta su propio hilo; es invocada por la API.
    """

    def __init__(self, interval_seconds: int = 15):
        self.logger = logging.getLogger("ComparisonLogger")
        self.interval = interval_seconds
        self._last_log_time = 0

        # Cargar configuración para warmup steps y exportación
        settings = load_app_settings()
        self.warmup_steps = settings.decision.entrenamiento_simplificado.warmup_steps
        self._warmup_completed = False

        # Configuración de exportación con timestamp único por sesión
        self.export_config = settings.sumo.comparacion_export
        self._db_connection: sqlite3.Connection | None = None

        # Generar ruta única para esta sesión (patrón similar a reportes)
        if self.export_config.enabled:
            base_dir = os.path.dirname(
                self.export_config.db_path
            )  # results/comparisons/
            session_timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            self._session_dir = os.path.join(
                base_dir, f"comparison_{session_timestamp}"
            )
            self._db_path = os.path.join(self._session_dir, "comparison.db")
            self._init_database()
        else:
            self._session_dir = ""
            self._db_path = ""

        # Almacenamiento de estadísticas
        self._report_count = 0
        self._stats: dict = {
            "s1": {"vehicles_sum": 0, "vehicles_measurements": [], "wait_times": []},
            "s2": {"vehicles_sum": 0, "vehicles_measurements": [], "wait_times": []},
        }
        # Para tiempos de espera, guardamos el último valor (ya acumulado por SUMO)
        self._last_wait_times = {"s1": 0.0, "s2": 0.0}

        # Variables para tiempo acumulado real - seguimiento incremental
        self._cumulative_wait_times = {"s1": 0.0, "s2": 0.0}
        self._previous_wait_times = {"s1": 0.0, "s2": 0.0}
        self.logger.info(
            f"Logger de comparación inicializado. Registrará métricas cada {self.interval} segundos de simulación."
        )
        self.logger.info(
            f"Periodo de warmup configurado: {self.warmup_steps} pasos iniciales se omitirán"
        )

        if self.export_config.enabled:
            self.logger.info(f"✅ Exportación habilitada: {self._db_path}")
            self.logger.info(f"📁 Directorio de sesión: {self._session_dir}")
        else:
            self.logger.info("⚠️ Exportación de comparaciones deshabilitada")

    def _init_database(self) -> None:
        """Inicializar la base de datos SQLite y crear las tablas necesarias."""
        try:
            # Crear directorio de sesión si no existe
            if not os.path.exists(self._session_dir):
                os.makedirs(self._session_dir)

            # Conectar a la base de datos
            self._db_connection = sqlite3.connect(
                self._db_path, check_same_thread=False
            )
            cursor = self._db_connection.cursor()

            # Crear tabla de métricas temporales (sin session_id ya que cada sesión tiene su propia DB)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS comparacion_metricas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_simulacion REAL NOT NULL,

                    -- Tiempos de espera S1 (DQN)
                    s1_tiempo_actual REAL,
                    s1_tiempo_acumulado REAL,
                    s1_tiempo_promedio REAL,
                    s1_tiempo_mediana REAL,
                    s1_tiempo_std REAL,
                    s1_tiempo_p95 REAL,

                    -- Tiempos de espera S2 (Fijo)
                    s2_tiempo_actual REAL,
                    s2_tiempo_acumulado REAL,
                    s2_tiempo_promedio REAL,
                    s2_tiempo_mediana REAL,
                    s2_tiempo_std REAL,
                    s2_tiempo_p95 REAL,

                    -- Vehículos S1 (DQN)
                    s1_vehiculos_actual INTEGER,
                    s1_vehiculos_acumulado INTEGER,
                    s1_vehiculos_promedio REAL,
                    s1_vehiculos_mediana REAL,
                    s1_vehiculos_std REAL,
                    s1_vehiculos_p95 REAL,

                    -- Vehículos S2 (Fijo)
                    s2_vehiculos_actual INTEGER,
                    s2_vehiculos_acumulado INTEGER,
                    s2_vehiculos_promedio REAL,
                    s2_vehiculos_mediana REAL,
                    s2_vehiculos_std REAL,
                    s2_vehiculos_p95 REAL,

                    generado_en TEXT NOT NULL
                )
            """
            )

            # Crear tabla de resúmenes finales (sin session_id, solo una fila por DB)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS comparacion_resumenes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_mediciones INTEGER NOT NULL,
                    mejora_tiempo_absoluta REAL,
                    mejora_tiempo_porcentual REAL,
                    mejora_vehiculos_absoluta REAL,
                    mejora_vehiculos_porcentual REAL,
                    s1_tiempo_final REAL,
                    s2_tiempo_final REAL,
                    s1_vehiculos_final REAL,
                    s2_vehiculos_final REAL,
                    session_completada_en TEXT NOT NULL
                )
            """
            )

            self._db_connection.commit()
            self.logger.info(f"🗃️ Base de datos inicializada: {self._db_path}")

        except Exception as e:
            self.logger.error(f"❌ Error inicializando base de datos: {e}")
            self._db_connection = None

    def _save_temporal_metrics(
        self, sim_time: float, app_s1: SumoApp, app_s2: SumoApp
    ) -> None:
        """Guardar métricas temporales en la base de datos."""
        if not self._db_connection:
            return

        try:
            # Calcular estadísticas actuales
            wait_stats_s1 = self._calculate_statistical_metrics(
                self._stats["s1"]["wait_times"]
            )
            wait_stats_s2 = self._calculate_statistical_metrics(
                self._stats["s2"]["wait_times"]
            )
            vehicle_stats_s1 = self._calculate_statistical_metrics(
                self._stats["s1"]["vehicles_measurements"]
            )
            vehicle_stats_s2 = self._calculate_statistical_metrics(
                self._stats["s2"]["vehicles_measurements"]
            )

            # Datos actuales
            t1 = app_s1.get_total_wait_time()
            t2 = app_s2.get_total_wait_time()
            zones_s1 = app_s1.get_vehicle_counts_by_zone()
            zones_s2 = app_s2.get_vehicle_counts_by_zone()
            v1 = sum(zones_s1.values())
            v2 = sum(zones_s2.values())

            cursor = self._db_connection.cursor()
            cursor.execute(
                """
                INSERT INTO comparacion_metricas (
                    timestamp_simulacion,
                    s1_tiempo_actual, s1_tiempo_acumulado, s1_tiempo_promedio, s1_tiempo_mediana, s1_tiempo_std, s1_tiempo_p95,
                    s2_tiempo_actual, s2_tiempo_acumulado, s2_tiempo_promedio, s2_tiempo_mediana, s2_tiempo_std, s2_tiempo_p95,
                    s1_vehiculos_actual, s1_vehiculos_acumulado, s1_vehiculos_promedio, s1_vehiculos_mediana, s1_vehiculos_std, s1_vehiculos_p95,
                    s2_vehiculos_actual, s2_vehiculos_acumulado, s2_vehiculos_promedio, s2_vehiculos_mediana, s2_vehiculos_std, s2_vehiculos_p95,
                    generado_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    sim_time,
                    # S1 tiempos
                    t1,
                    self._cumulative_wait_times["s1"],
                    wait_stats_s1["mean"],
                    wait_stats_s1["median"],
                    wait_stats_s1["std"],
                    wait_stats_s1["p95"],
                    # S2 tiempos
                    t2,
                    self._cumulative_wait_times["s2"],
                    wait_stats_s2["mean"],
                    wait_stats_s2["median"],
                    wait_stats_s2["std"],
                    wait_stats_s2["p95"],
                    # S1 vehículos
                    v1,
                    self._stats["s1"]["vehicles_sum"],
                    vehicle_stats_s1["mean"],
                    vehicle_stats_s1["median"],
                    vehicle_stats_s1["std"],
                    vehicle_stats_s1["p95"],
                    # S2 vehículos
                    v2,
                    self._stats["s2"]["vehicles_sum"],
                    vehicle_stats_s2["mean"],
                    vehicle_stats_s2["median"],
                    vehicle_stats_s2["std"],
                    vehicle_stats_s2["p95"],
                    # Metadata
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            self._db_connection.commit()

        except Exception as e:
            self.logger.error(f"❌ Error guardando métricas temporales: {e}")

    def _save_final_summary(self) -> None:
        """Guardar resumen final en la base de datos."""
        if not self._db_connection or self._report_count == 0:
            return

        try:
            # Calcular mejoras finales
            total_wait_s1 = self._cumulative_wait_times["s1"]
            total_wait_s2 = self._cumulative_wait_times["s2"]

            vehicle_stats_s1 = self._calculate_statistical_metrics(
                self._stats["s1"]["vehicles_measurements"]
            )
            vehicle_stats_s2 = self._calculate_statistical_metrics(
                self._stats["s2"]["vehicles_measurements"]
            )

            # Calcular mejoras
            if total_wait_s2 > 0:
                wait_improvement_abs = total_wait_s2 - total_wait_s1
                wait_improvement_pct = (wait_improvement_abs / total_wait_s2) * 100
            else:
                wait_improvement_abs = 0.0
                wait_improvement_pct = 0.0

            if vehicle_stats_s2["mean"] > 0:
                vehicles_improvement_abs = (
                    vehicle_stats_s2["mean"] - vehicle_stats_s1["mean"]
                )
                vehicles_improvement_pct = (
                    vehicles_improvement_abs / vehicle_stats_s2["mean"]
                ) * 100
            else:
                vehicles_improvement_abs = 0.0
                vehicles_improvement_pct = 0.0

            cursor = self._db_connection.cursor()
            cursor.execute(
                """
                INSERT INTO comparacion_resumenes (
                    total_mediciones,
                    mejora_tiempo_absoluta, mejora_tiempo_porcentual,
                    mejora_vehiculos_absoluta, mejora_vehiculos_porcentual,
                    s1_tiempo_final, s2_tiempo_final,
                    s1_vehiculos_final, s2_vehiculos_final,
                    session_completada_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self._report_count,
                    wait_improvement_abs,
                    wait_improvement_pct,
                    vehicles_improvement_abs,
                    vehicles_improvement_pct,
                    total_wait_s1,
                    total_wait_s2,
                    vehicle_stats_s1["mean"],
                    vehicle_stats_s2["mean"],
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            self._db_connection.commit()
            self.logger.info("💾 Resumen final guardado en base de datos")

        except Exception as e:
            self.logger.error(f"❌ Error guardando resumen final: {e}")

    def __del__(self) -> None:
        """Cerrar conexión de base de datos al destruir el objeto."""
        if self._db_connection:
            self._db_connection.close()

    def log_if_needed(self, app_s1: SumoApp, app_s2: SumoApp) -> None:
        """
        Verifica si ha pasado suficiente tiempo de simulación para registrar
        un nuevo punto de comparación.
        """
        current_time = app_s1.traci.simulation.getTime()

        # Verificar periodo de warmup
        if current_time < self.warmup_steps:
            if not self._warmup_completed:
                # Solo mostrar mensaje una vez cada cierto tiempo durante warmup
                if int(current_time) % 30 == 0 and current_time > 0:  # Cada 30 segundos
                    self.logger.info(
                        f"Periodo de warmup: {current_time:.0f}s/{self.warmup_steps}s - Sin metricas aun"
                    )
            return

        # Marcar warmup como completado y mostrar mensaje
        if not self._warmup_completed:
            self._warmup_completed = True
            self.logger.info(
                f"Warmup completado en t={current_time:.0f}s - Iniciando registro de metricas"
            )

        # Si el tiempo actual ha cruzado un nuevo umbral del intervalo
        if current_time // self.interval > self._last_log_time // self.interval:
            self._last_log_time = current_time
            self._log_comparison(current_time, app_s1, app_s2)

    def _calculate_statistical_metrics(self, data: list) -> dict:
        """
        Calcula métricas estadísticas avanzadas para una lista de datos.

        Returns:
            dict con mean, median, std, p95
        """
        if not data:
            return {"mean": 0.0, "median": 0.0, "std": 0.0, "p95": 0.0}

        data_array = np.array(data)
        return {
            "mean": float(np.mean(data_array)),
            "median": float(np.median(data_array)),
            "std": float(np.std(data_array)),
            "p95": float(np.percentile(data_array, 95)),
        }

    def _log_comparison(
        self, sim_time: float, app_s1: SumoApp, app_s2: SumoApp
    ) -> None:
        """Recopila y registra las métricas comparativas."""
        self._report_count += 1

        # --- Tiempos de espera ---
        # get_total_wait_time() devuelve tiempo TOTAL acumulado desde inicio de simulación
        t1 = app_s1.get_total_wait_time()
        t2 = app_s2.get_total_wait_time()

        # Calcular incremento desde la última medición para tiempo acumulado real
        t1_increment = max(0, t1 - self._previous_wait_times["s1"])
        t2_increment = max(0, t2 - self._previous_wait_times["s2"])

        # Actualizar tiempo acumulado con incrementos
        self._cumulative_wait_times["s1"] += t1_increment
        self._cumulative_wait_times["s2"] += t2_increment

        # Actualizar valores previos para próxima medición
        self._previous_wait_times["s1"] = t1
        self._previous_wait_times["s2"] = t2

        # Guardar tiempos para cálculo de promedio
        self._stats["s1"]["wait_times"].append(t1)
        self._stats["s2"]["wait_times"].append(t2)

        # Actualizar últimos valores acumulados
        self._last_wait_times["s1"] = t1
        self._last_wait_times["s2"] = t2

        # --- Cantidad de vehículos en zonas ---
        # Obtener suma de vehículos en todas las zonas en este momento
        zones_s1 = app_s1.get_vehicle_counts_by_zone()
        zones_s2 = app_s2.get_vehicle_counts_by_zone()
        v1 = sum(zones_s1.values())  # Vehículos actuales S1
        v2 = sum(zones_s2.values())  # Vehículos actuales S2

        # Guardar mediciones para calcular promedio temporal real
        self._stats["s1"]["vehicles_measurements"].append(v1)
        self._stats["s2"]["vehicles_measurements"].append(v2)
        self._stats["s1"]["vehicles_sum"] += v1
        self._stats["s2"]["vehicles_sum"] += v2

        # Calcular métricas estadísticas avanzadas
        wait_stats_s1 = self._calculate_statistical_metrics(
            self._stats["s1"]["wait_times"]
        )
        wait_stats_s2 = self._calculate_statistical_metrics(
            self._stats["s2"]["wait_times"]
        )
        vehicle_stats_s1 = self._calculate_statistical_metrics(
            self._stats["s1"]["vehicles_measurements"]
        )
        vehicle_stats_s2 = self._calculate_statistical_metrics(
            self._stats["s2"]["vehicles_measurements"]
        )

        # Calcular suma acumulada de vehículos
        total_v1 = self._stats["s1"]["vehicles_sum"]
        total_v2 = self._stats["s2"]["vehicles_sum"]

        self.logger.info("=" * 75)
        self.logger.info(f"COMPARATIVA t={sim_time:.0f}s")
        self.logger.info(
            f"Tiempo espera actual: S1(DQN)={t1:.2f}s | S2(Fijo)={t2:.2f}s"
        )
        self.logger.info(
            f"Tiempo espera acumulado: S1(DQN)={self._cumulative_wait_times['s1']:.2f}s | S2(Fijo)={self._cumulative_wait_times['s2']:.2f}s"
        )
        self.logger.info(
            f"Tiempo espera promedio: S1(DQN)={wait_stats_s1['mean']:.2f}s | S2(Fijo)={wait_stats_s2['mean']:.2f}s"
        )
        self.logger.info(
            f"Tiempo espera mediana: S1(DQN)={wait_stats_s1['median']:.2f}s | S2(Fijo)={wait_stats_s2['median']:.2f}s"
        )
        self.logger.info(
            f"Tiempo espera std: S1(DQN)={wait_stats_s1['std']:.2f}s | S2(Fijo)={wait_stats_s2['std']:.2f}s"
        )
        self.logger.info(
            f"Tiempo espera p95: S1(DQN)={wait_stats_s1['p95']:.2f}s | S2(Fijo)={wait_stats_s2['p95']:.2f}s"
        )
        self.logger.info(f"Vehiculos actuales: S1(DQN)={v1} | S2(Fijo)={v2}")
        self.logger.info(
            f"Vehiculos acumulados: S1(DQN)={total_v1} | S2(Fijo)={total_v2}"
        )
        self.logger.info(
            f"Vehiculos promedio: S1(DQN)={vehicle_stats_s1['mean']:.2f} | S2(Fijo)={vehicle_stats_s2['mean']:.2f}"
        )
        self.logger.info(
            f"Vehiculos mediana: S1(DQN)={vehicle_stats_s1['median']:.2f} | S2(Fijo)={vehicle_stats_s2['median']:.2f}"
        )
        self.logger.info(
            f"Vehiculos std: S1(DQN)={vehicle_stats_s1['std']:.2f} | S2(Fijo)={vehicle_stats_s2['std']:.2f}"
        )
        self.logger.info(
            f"Vehiculos p95: S1(DQN)={vehicle_stats_s1['p95']:.2f} | S2(Fijo)={vehicle_stats_s2['p95']:.2f}"
        )
        self.logger.info("=" * 75)

        # Guardar métricas en base de datos si está habilitada
        if self.export_config.enabled:
            self._save_temporal_metrics(sim_time, app_s1, app_s2)

    def log_final_comparative_summary(self) -> None:
        """
        Muestra un resumen final con las métricas comparativas y mejoras porcentuales.
        Debe llamarse al final de la simulación para mostrar el análisis completo.
        """
        if self._report_count == 0:
            self.logger.warning(
                "No hay datos de comparacion para mostrar resumen final"
            )
            return

        # Calcular métricas estadísticas finales
        wait_stats_s1 = self._calculate_statistical_metrics(
            self._stats["s1"]["wait_times"]
        )
        wait_stats_s2 = self._calculate_statistical_metrics(
            self._stats["s2"]["wait_times"]
        )
        vehicle_stats_s1 = self._calculate_statistical_metrics(
            self._stats["s1"]["vehicles_measurements"]
        )
        vehicle_stats_s2 = self._calculate_statistical_metrics(
            self._stats["s2"]["vehicles_measurements"]
        )

        # Tiempos de espera: usar valores acumulados reales (seguimiento incremental)
        total_wait_s1 = self._cumulative_wait_times["s1"]
        total_wait_s2 = self._cumulative_wait_times["s2"]

        # Vehículos acumulados totales
        total_vehicles_s1 = self._stats["s1"]["vehicles_sum"]
        total_vehicles_s2 = self._stats["s2"]["vehicles_sum"]

        # Calcular promedios
        avg_wait_s1 = wait_stats_s1["mean"] if self._report_count > 0 else 0.0
        avg_wait_s2 = wait_stats_s2["mean"] if self._report_count > 0 else 0.0
        avg_vehicles_s1 = vehicle_stats_s1["mean"] if self._report_count > 0 else 0.0
        avg_vehicles_s2 = vehicle_stats_s2["mean"] if self._report_count > 0 else 0.0

        # Calcular mejoras porcentuales con protección contra división por cero
        if total_wait_s2 > 0:
            wait_improvement_abs = total_wait_s2 - total_wait_s1
            wait_improvement_pct = (wait_improvement_abs / total_wait_s2) * 100
        else:
            wait_improvement_abs = 0.0
            wait_improvement_pct = 0.0

        if vehicle_stats_s2["mean"] > 0:
            vehicles_improvement_abs = (
                vehicle_stats_s2["mean"] - vehicle_stats_s1["mean"]
            )
            vehicles_improvement_pct = (
                vehicles_improvement_abs / vehicle_stats_s2["mean"]
            ) * 100
        else:
            vehicles_improvement_abs = 0.0
            vehicles_improvement_pct = 0.0

        # Mostrar resumen final con formato auto-descriptivo
        self.logger.info("=" * 80)
        self.logger.info("RESUMEN FINAL - METRICAS COMPARATIVAS")
        self.logger.info("=" * 80)
        self.logger.info(
            f"Mediciones totales: {self._report_count} puntos de comparacion"
        )
        self.logger.info(
            f"Tiempo espera acumulado: S1(DQN)={total_wait_s1:.2f}s | S2(Fijo)={total_wait_s2:.2f}s"
        )
        self.logger.info(
            f"Tiempo espera promedio: S1(DQN)={avg_wait_s1:.2f}s | S2(Fijo)={avg_wait_s2:.2f}s"
        )
        self.logger.info(
            f"Vehiculos acumulados: S1(DQN)={total_vehicles_s1} | S2(Fijo)={total_vehicles_s2}"
        )
        self.logger.info(
            f"Vehiculos promedio: S1(DQN)={avg_vehicles_s1:.2f} | S2(Fijo)={avg_vehicles_s2:.2f}"
        )

        # Agregar métricas estadísticas avanzadas
        if self._report_count > 0:
            # Calcular estadísticas para cada métrica
            wait_stats_s1 = self._calculate_statistical_metrics(
                self._stats["s1"]["wait_times"]
            )
            wait_stats_s2 = self._calculate_statistical_metrics(
                self._stats["s2"]["wait_times"]
            )
            vehicle_stats_s1 = self._calculate_statistical_metrics(
                self._stats["s1"]["vehicles_measurements"]
            )
            vehicle_stats_s2 = self._calculate_statistical_metrics(
                self._stats["s2"]["vehicles_measurements"]
            )

            # Estadísticas de tiempo de espera
            self.logger.info(
                f"Tiempo espera - Mediana: S1(DQN)={wait_stats_s1['median']:.2f}s | S2(Fijo)={wait_stats_s2['median']:.2f}s"
            )
            self.logger.info(
                f"Tiempo espera - Desv.Est: S1(DQN)={wait_stats_s1['std']:.2f}s | S2(Fijo)={wait_stats_s2['std']:.2f}s"
            )
            self.logger.info(
                f"Tiempo espera - P95: S1(DQN)={wait_stats_s1['p95']:.2f}s | S2(Fijo)={wait_stats_s2['p95']:.2f}s"
            )

            # Estadísticas de vehículos
            self.logger.info(
                f"Vehiculos - Mediana: S1(DQN)={vehicle_stats_s1['median']:.1f} | S2(Fijo)={vehicle_stats_s2['median']:.1f}"
            )
            self.logger.info(
                f"Vehiculos - Desv.Est: S1(DQN)={vehicle_stats_s1['std']:.1f} | S2(Fijo)={vehicle_stats_s2['std']:.1f}"
            )
            self.logger.info(
                f"Vehiculos - P95: S1(DQN)={vehicle_stats_s1['p95']:.1f} | S2(Fijo)={vehicle_stats_s2['p95']:.1f}"
            )

            self.logger.info("-" * 80)

        if wait_improvement_abs > 0:
            self.logger.info(
                f"Mejora tiempo espera: DQN redujo {wait_improvement_abs:.2f}s ({wait_improvement_pct:.1f}%)"
            )
        elif wait_improvement_abs < 0:
            self.logger.info(
                f"Empeoramiento tiempo espera: DQN aumento {abs(wait_improvement_abs):.2f}s ({abs(wait_improvement_pct):.1f}%)"
            )
        else:
            self.logger.info("Mejora tiempo espera: Sin diferencia significativa")

        if vehicles_improvement_abs > 0:
            self.logger.info(
                f"Mejora vehiculos: DQN redujo {vehicles_improvement_abs:.1f} vehiculos ({vehicles_improvement_pct:.1f}%)"
            )
        elif vehicles_improvement_abs < 0:
            self.logger.info(
                f"Empeoramiento vehiculos: DQN aumento {abs(vehicles_improvement_abs):.1f} vehiculos ({abs(vehicles_improvement_pct):.1f}%)"
            )
        else:
            self.logger.info("Mejora vehiculos: Sin diferencia significativa")

        self.logger.info("=" * 80)

        # Guardar resumen final en base de datos si está habilitada
        if self.export_config.enabled:
            self._save_final_summary()
