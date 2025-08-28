import logging

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

    def log_if_needed(self, app_s1: SumoApp, app_s2: SumoApp) -> None:
        """
        Verifica si ha pasado suficiente tiempo de simulación para registrar
        un nuevo punto de comparación.
        """
        current_time = app_s1.traci.simulation.getTime()

        # Si el tiempo actual ha cruzado un nuevo umbral del intervalo
        if current_time // self.interval > self._last_log_time // self.interval:
            self._last_log_time = current_time
            self._log_comparison(current_time, app_s1, app_s2)

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

        # Calcular promedios de tiempo de espera
        avg_wait_s1 = (
            sum(self._stats["s1"]["wait_times"]) / len(self._stats["s1"]["wait_times"])
            if self._stats["s1"]["wait_times"]
            else 0
        )
        avg_wait_s2 = (
            sum(self._stats["s2"]["wait_times"]) / len(self._stats["s2"]["wait_times"])
            if self._stats["s2"]["wait_times"]
            else 0
        )

        # Calcular promedios de vehículos
        avg_v1 = (
            self._stats["s1"]["vehicles_sum"] / self._report_count
            if self._report_count > 0
            else 0
        )
        avg_v2 = (
            self._stats["s2"]["vehicles_sum"] / self._report_count
            if self._report_count > 0
            else 0
        )

        self.logger.info("=" * 75)
        self.logger.info(f"COMPARATIVA t={sim_time:.0f}s")
        self.logger.info(
            f"Tiempo espera actual: S1(DQN)={t1:.2f}s | S2(Fijo)={t2:.2f}s"
        )
        self.logger.info(
            f"Tiempo espera acumulado: S1(DQN)={self._cumulative_wait_times['s1']:.2f}s | S2(Fijo)={self._cumulative_wait_times['s2']:.2f}s"
        )
        self.logger.info(
            f"Tiempo espera promedio: S1(DQN)={avg_wait_s1:.2f}s | S2(Fijo)={avg_wait_s2:.2f}s"
        )
        self.logger.info(f"Vehiculos actuales: S1(DQN)={v1} | S2(Fijo)={v2}")
        self.logger.info(
            f"Vehiculos acumulados: S1(DQN)={self._stats['s1']['vehicles_sum']} | S2(Fijo)={self._stats['s2']['vehicles_sum']}"
        )
        self.logger.info(
            f"Vehiculos promedio: S1(DQN)={avg_v1:.2f} | S2(Fijo)={avg_v2:.2f}"
        )
        self.logger.info("=" * 75)

    def log_final_comparative_summary(self) -> None:
        """
        Muestra un resumen final con las métricas comparativas y mejoras porcentuales.
        Debe llamarse al final de la simulación para mostrar el análisis completo.
        """
        if self._report_count == 0:
            self.logger.warning(
                "⚠️ No hay datos de comparación para mostrar resumen final"
            )
            return

        # Calcular métricas finales correctamente
        # Tiempos de espera: usar valores acumulados reales (seguimiento incremental)
        total_wait_s1 = self._cumulative_wait_times["s1"]
        total_wait_s2 = self._cumulative_wait_times["s2"]

        # Calcular promedio de tiempos de espera
        avg_wait_s1 = (
            sum(self._stats["s1"]["wait_times"]) / len(self._stats["s1"]["wait_times"])
            if self._stats["s1"]["wait_times"]
            else 0.0
        )
        avg_wait_s2 = (
            sum(self._stats["s2"]["wait_times"]) / len(self._stats["s2"]["wait_times"])
            if self._stats["s2"]["wait_times"]
            else 0.0
        )

        # Vehículos: promedio temporal real
        avg_vehicles_s1 = (
            float(self._stats["s1"]["vehicles_sum"]) / self._report_count
            if self._report_count > 0
            else 0.0
        )
        avg_vehicles_s2 = (
            float(self._stats["s2"]["vehicles_sum"]) / self._report_count
            if self._report_count > 0
            else 0.0
        )

        # Vehículos acumulados totales
        total_vehicles_s1 = self._stats["s1"]["vehicles_sum"]
        total_vehicles_s2 = self._stats["s2"]["vehicles_sum"]

        # Calcular mejoras porcentuales con protección contra división por cero
        if total_wait_s2 > 0:
            wait_improvement_abs = total_wait_s2 - total_wait_s1
            wait_improvement_pct = (wait_improvement_abs / total_wait_s2) * 100
        else:
            wait_improvement_abs = 0.0
            wait_improvement_pct = 0.0

        if avg_vehicles_s2 > 0:
            vehicles_improvement_abs = avg_vehicles_s2 - avg_vehicles_s1
            vehicles_improvement_pct = (
                vehicles_improvement_abs / avg_vehicles_s2
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
