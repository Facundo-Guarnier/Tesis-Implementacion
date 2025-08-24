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
            "s1": {"vehicles_sum": 0, "vehicles_measurements": []},
            "s2": {"vehicles_sum": 0, "vehicles_measurements": []},
        }
        # Para tiempos de espera, guardamos el último valor (ya acumulado por SUMO)
        self._last_wait_times = {"s1": 0.0, "s2": 0.0}
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
        # get_total_wait_time() devuelve tiempo TOTAL acumulado desde inicio de simulación
        # Solo guardamos el último valor, no sumamos (para evitar duplicación)
        t1 = app_s1.get_total_wait_time()
        t2 = app_s2.get_total_wait_time()
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
            f" Acumulado S1: {self._last_wait_times['s1']:.2f}s | Acumulado S2: {self._last_wait_times['s2']:.2f}s"
        )
        # Los tiempos ya son acumulados, no calculamos promedio aquí
        self.logger.info(
            "----------------------- Vehiculos en zonas --------------------------------"
        )
        self.logger.info(f" S1 (API): {v1}  |  S2 (Normal): {v2}")
        self.logger.info(
            f" Suma acumulada S1: {self._stats['s1']['vehicles_sum']} | Suma acumulada S2: {self._stats['s2']['vehicles_sum']}"
        )
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
        self.logger.info(f" Promedio S1: {avg_v1:.2f} | Promedio S2: {avg_v2:.2f}")
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
        # Tiempos de espera: usar últimos valores (ya son acumulados por SUMO)
        total_wait_s1 = self._last_wait_times["s1"]
        total_wait_s2 = self._last_wait_times["s2"]

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

        # Mostrar resumen final
        self.logger.info("=" * 80)
        self.logger.info("📈 === RESUMEN FINAL - MÉTRICAS COMPARATIVAS ===")
        self.logger.info("=" * 80)
        self.logger.info("⏱️  TIEMPO DE ESPERA ACUMULADO:")
        self.logger.info(
            f"    S1 (DQN): {total_wait_s1:.2f}s | S2 (Tiempos Fijos): {total_wait_s2:.2f}s"
        )

        if wait_improvement_abs > 0:
            self.logger.info(
                f"    ✅ Reducción DQN: -{wait_improvement_abs:.2f}s (-{wait_improvement_pct:.1f}%)"
            )
        elif wait_improvement_abs < 0:
            self.logger.info(
                f"    ❌ Aumento DQN: +{abs(wait_improvement_abs):.2f}s (+{abs(wait_improvement_pct):.1f}%)"
            )
        else:
            self.logger.info("    ➖ Sin diferencia en tiempo de espera")

        self.logger.info("")
        self.logger.info("🚗 PROMEDIO VEHÍCULOS EN SISTEMA:")
        self.logger.info(
            f"    S1 (DQN): {avg_vehicles_s1:.1f} | S2 (Tiempos Fijos): {avg_vehicles_s2:.1f}"
        )

        if vehicles_improvement_abs > 0:
            self.logger.info(
                f"    ✅ Reducción DQN: -{vehicles_improvement_abs:.1f} (-{vehicles_improvement_pct:.1f}%)"
            )
        elif vehicles_improvement_abs < 0:
            self.logger.info(
                f"    ❌ Aumento DQN: +{abs(vehicles_improvement_abs):.1f} (+{abs(vehicles_improvement_pct):.1f}%)"
            )
        else:
            self.logger.info("    ➖ Sin diferencia en promedio de vehículos")

        self.logger.info("")
        self.logger.info(
            f"📊 Mediciones tomadas: {self._report_count} puntos de comparación"
        )
        self.logger.info("=" * 80)
