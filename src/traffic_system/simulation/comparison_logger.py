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
        self._stats = {
            "s1": {"wait_time": 0.0, "vehicles": 0},
            "s2": {"wait_time": 0.0, "vehicles": 0},
        }
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

        # --- Verificar sincronización ---
        time_s1 = app_s1.traci.simulation.getTime()
        time_s2 = app_s2.traci.simulation.getTime()
        time_difference = abs(time_s1 - time_s2)

        # Aplicar la misma lógica de sincronización que en la API
        if max(time_s1, time_s2) < 5.0:
            is_synchronized = time_difference <= 2.0
            sync_status = (
                "✅ SINCRONIZADO (fase inicial)"
                if is_synchronized
                else "❌ DESINCRONIZADO"
            )
        else:
            is_synchronized = time_difference <= 1.0
            sync_status = "✅ SINCRONIZADO" if is_synchronized else "❌ DESINCRONIZADO"

        # --- Tiempos de espera ---
        t1 = app_s1.get_total_wait_time()
        t2 = app_s2.get_total_wait_time()
        self._stats["s1"]["wait_time"] += t1
        self._stats["s2"]["wait_time"] += t2

        # --- Cantidad de vehículos en zonas ---
        # Obtener suma de vehículos en todas las zonas (no total de simulación)
        zones_s1 = app_s1.get_vehicle_counts_by_zone()
        zones_s2 = app_s2.get_vehicle_counts_by_zone()
        v1 = sum(zones_s1.values())  # Suma de vehículos en todas las zonas S1
        v2 = sum(zones_s2.values())  # Suma de vehículos en todas las zonas S2
        self._stats["s1"]["vehicles"] += v1
        self._stats["s2"]["vehicles"] += v2

        # --- Logging ---
        self.logger.info("=" * 75)
        self.logger.info(
            f" COMPARATIVA en t ~ {sim_time:.0f}s (Reporte #{self._report_count})"
        )
        self.logger.info(
            "----------------------- Estado de sincronización --------------------------"
        )
        self.logger.info(
            f" S1: {time_s1:.1f}s | S2: {time_s2:.1f}s | Diff: {time_difference:.1f}s | {sync_status}"
        )
        self.logger.info(
            "----------------------- Tiempo de espera total ----------------------------"
        )
        self.logger.info(f" S1 (API): {t1:.2f}s  |  S2 (Normal): {t2:.2f}s")
        self.logger.info(
            f" Acumulado S1: {self._stats['s1']['wait_time']:.2f}s | Acumulado S2: {self._stats['s2']['wait_time']:.2f}s"
        )
        self.logger.info(
            f" Promedio S1: {self._stats['s1']['wait_time']/self._report_count:.2f}s | Promedio S2: {self._stats['s2']['wait_time']/self._report_count:.2f}s"
        )
        self.logger.info(
            "----------------------- Vehiculos en zonas --------------------------------"
        )
        self.logger.info(f" S1 (API): {v1}  |  S2 (Normal): {v2}")
        self.logger.info(
            f" Acumulado S1: {self._stats['s1']['vehicles']} | Acumulado S2: {self._stats['s2']['vehicles']}"
        )
        self.logger.info(
            f" Promedio S1: {self._stats['s1']['vehicles']/self._report_count:.2f} | Promedio S2: {self._stats['s2']['vehicles']/self._report_count:.2f}"
        )
        self.logger.info("=" * 75)
