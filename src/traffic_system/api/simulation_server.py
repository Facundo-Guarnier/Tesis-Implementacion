import logging

from flask import Flask, Response, jsonify, request

from src.traffic_system.simulation.app import SumoApp


class SumoAPI(Flask):
    def __init__(
        self,
        name: str,
        app_s1: SumoApp,
        app_s2: SumoApp | None = None,
        comparison_logger=None,
    ) -> None:
        super().__init__(name)

        self.app_s1 = app_s1
        self.app_s2 = app_s2
        self.comparison_logger = comparison_logger

        self.logger = logging.getLogger("SumoAPI")

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        self.route("/espera", methods=["GET"])(self.get_wait_times)
        self.route("/espera2", methods=["GET"])(self.get_wait_times_s2)
        self.route("/espera/<zone_id>", methods=["GET"])(self.get_zone_wait_time)
        self.route("/sincronizacion", methods=["GET"])(self.get_synchronization_status)

        self.route("/avanzar", methods=["PUT"])(self.step_simulation)
        self.route("/semaforo", methods=["GET"])(self.get_all_traffic_light_states)
        self.route("/semaforo", methods=["PUT"])(self.set_all_traffic_light_states)
        self.route("/semaforo/<light_id>", methods=["GET"])(
            self.get_traffic_light_state
        )
        self.route("/semaforo/<light_id>", methods=["PUT"])(
            self.set_traffic_light_state
        )
        self.route("/simulacion", methods=["GET"])(self.get_simulation_status)
        self.route("/simulacion/reiniciar", methods=["POST"])(self.reset_simulations)
        self.route("/reporte", methods=["GET"])(self.get_report)

    def step_simulation(self) -> tuple[Response, int]:
        """
        Avanzar la simulación. Este es ahora el punto de control central.
        Avanza s1 y, si existe, s2 de forma sincronizada.
        """
        steps = request.args.get("steps", type=int)
        if not steps:
            return jsonify({"error": "Falta el parámetro 'steps'."}), 400

        # Verificar estado inicial de ambas simulaciones
        # Solo aplicar verificación estricta después de los primeros pasos
        if self.app_s2:
            time_s1 = self.app_s1.traci.simulation.getTime()
            time_s2 = self.app_s2.traci.simulation.getTime()

            # Si estamos en los primeros pasos, permitir diferencias mayores
            if max(time_s1, time_s2) >= 5.0 and not self._check_synchronization():
                return jsonify({"error": "Las simulaciones están desincronizadas"}), 500

        # Avanzar simulación principal (controlada por el agente)
        done_s1 = self.app_s1.advance(steps=steps)
        done_s2 = False

        # Si estamos en modo comparación, avanzar la segunda simulación
        # por la misma cantidad de pasos para mantenerla sincronizada.
        if self.app_s2:
            try:
                done_s2 = self.app_s2.advance(steps=steps)

                # Verificar que ambas simulaciones siguen sincronizadas
                # Solo mostrar warning después de los primeros pasos
                tiempo_s1_final = self.app_s1.traci.simulation.getTime()
                if tiempo_s1_final >= 5.0 and not self._check_synchronization():
                    self.logger.warning(
                        "Las simulaciones se desincronizaron durante el avance"
                    )

            except Exception as e:
                self.logger.error(f"Error avanzando simulación de comparación: {e}")
                return (
                    jsonify({"error": f"Error en simulación de comparación: {str(e)}"}),
                    500,
                )

        # Si hay un logger de comparación, invocarlo para que verifique
        # si debe registrar las métricas.
        if self.comparison_logger and self.app_s2:
            self.comparison_logger.log_if_needed(self.app_s1, self.app_s2)

        # La simulación se considera terminada si cualquiera de las dos termina
        done = done_s1 or done_s2

        return (
            jsonify(
                {
                    "done": done,
                    "s1_done": done_s1,
                    "s2_done": done_s2 if self.app_s2 else None,
                    "sync_status": (
                        "ok"
                        if not self.app_s2 or self._check_synchronization()
                        else "desync"
                    ),
                }
            ),
            200,
        )

    def _check_synchronization(self) -> bool:
        """
        Verifica que ambas simulaciones estén sincronizadas (en el mismo paso de tiempo).
        Permite una diferencia máxima de 1 paso como se especificó.
        En los primeros pasos (t < 5s), es más permisivo para permitir la sincronización inicial.
        """
        if not self.app_s2:
            return True

        try:
            time_s1: float = self.app_s1.traci.simulation.getTime()
            time_s2: float = self.app_s2.traci.simulation.getTime()
            difference: float = abs(time_s1 - time_s2)

            # Ser más permisivo en los primeros pasos para permitir sincronización inicial
            if max(time_s1, time_s2) < 5.0:
                # En los primeros 5 segundos, permitir hasta 2 segundos de diferencia
                is_synced: bool = difference <= 2.0
                if not is_synced:
                    self.logger.info(
                        f"Sincronización inicial: S1={time_s1 :.1f}s, S2={time_s2:.1f}s, diff={difference :.1f}s (permitido en fase inicial)"
                    )
            else:
                # Después de los primeros 5 segundos, aplicar la regla normal
                is_synced = difference <= 1.0
                if not is_synced:
                    self.logger.warning(
                        f"Simulaciones desincronizadas: S1={time_s1 :.1f}s, S2={time_s2:.1f}s, diff={difference :.1f}s"
                    )

            return is_synced

        except Exception as e:
            self.logger.error(f"Error verificando sincronización: {e}")
            return False

    def get_synchronization_status(self) -> tuple[Response, int]:
        """
        Endpoint para obtener información de sincronización entre las dos simulaciones.
        """
        if not self.app_s2:
            return jsonify({"error": "No hay simulación de comparación activa"}), 404

        try:
            time_s1: float = self.app_s1.traci.simulation.getTime()
            time_s2: float = self.app_s2.traci.simulation.getTime()
            difference: float = abs(time_s1 - time_s2)

            # Aplicar la misma lógica de sincronización que en _verificar_sincronizacion
            if max(time_s1, time_s2) < 5.0:
                is_synced = difference <= 2.0
                max_allowed_difference = 2.0
                phase = "inicial"
            else:
                is_synced = difference <= 1.0
                max_allowed_difference = 1.0
                phase = "normal"

            return (
                jsonify(
                    {
                        "sincronizado": is_synced,
                        "tiempo_s1": time_s1,
                        "tiempo_s2": time_s2,
                        "diferencia": difference,
                        "max_diferencia_permitida": max_allowed_difference,
                        "fase": phase,
                    }
                ),
                200,
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo sincronización: {e}")
            return jsonify({"error": str(e)}), 500

    # --- El resto de los métodos de la API no necesitan cambios ---
    # ... (getTiemposEspera, getEstados, etc. se quedan como estaban)
    def get_wait_times(self) -> tuple[Response, int]:
        """Obtener tiempos de espera de la simulación principal (S1)."""
        return (
            jsonify(
                {
                    "tiempo_espera_total": self.app_s1.get_total_wait_time(),
                    "tiempos_espera": self.app_s1.get_wait_times(),
                }
            ),
            200,
        )

    def get_wait_times_s2(self) -> tuple[Response, int]:
        """Obtener tiempos de espera de la simulación de comparación (S2)."""
        if self.app_s2 and self.app_s2.is_simulation_active():
            return (
                jsonify(
                    {
                        "tiempo_espera_total": self.app_s2.get_total_wait_time(),
                        "tiempos_espera": self.app_s2.get_wait_times(),
                    }
                ),
                200,
            )
        return jsonify({"error": "Simulación de comparación no disponible."}), 404

    def get_zone_wait_time(self, zone_id: str) -> tuple[Response, int]:
        """Obtener tiempo de espera de una zona en S1."""
        return (
            jsonify({"tiempo_espera": self.app_s1.get_zone_wait_time(zone_id=zone_id)}),
            200,
        )

    def get_all_traffic_light_states(self) -> tuple[Response, int]:
        """Obtener estados de semáforos de S1."""
        return jsonify({"estados": self.app_s1.get_traffic_light_states()}), 200

    def get_traffic_light_state(self, id: str) -> tuple[Response, int]:
        """Obtener estado de un semáforo de S1."""
        return jsonify({"estado": self.app_s1.get_traffic_light_state(id)}), 200

    def set_traffic_light_state(self, light_id) -> tuple[Response, int]:
        """Cambiar el estado de un semáforo en S1."""
        state = request.args.get("estado", type=str)
        if not state:
            return jsonify({"error": "Falta el parámetro 'estado'."}), 400

        try:
            # Capturar tiempo antes del cambio
            time_s1_before = self.app_s1.traci.simulation.getTime()

            # Cambiar estado del semáforo en S1 (esto puede avanzar 3 pasos internamente)
            self.app_s1.set_traffic_light_state(light_id, state)

            # Si hay simulación de comparación, sincronizar el avance
            if self.app_s2:
                time_s1_after = self.app_s1.traci.simulation.getTime()
                steps_advanced = time_s1_after - time_s1_before

                if steps_advanced > 0:
                    self.logger.debug(
                        f"S1 avanzó {steps_advanced:.1f} pasos por cambio de semáforo {light_id}. "
                        f"Sincronizando S2..."
                    )
                    # Hacer que S2 avance los mismos pasos para mantenerse sincronizada
                    self.app_s2.advance(int(steps_advanced))

            return jsonify({"estado": state}), 200

        except Exception as e:
            self.logger.error(f"Error cambiando estado de semáforo {light_id}: {e}")
            return jsonify({"error": f"Error interno: {str(e)}"}), 500

    def set_all_traffic_light_states(self) -> tuple[Response, int]:
        """Cambiar los estados de varios semáforos en S1."""
        payload = request.json
        if not payload or "data" not in payload:
            return jsonify({"error": "Falta el campo 'data' en el JSON."}), 400

        try:
            # Capturar tiempo antes del cambio
            time_s1_before = self.app_s1.traci.simulation.getTime()

            # Cambiar estados de semáforos en S1 (esto puede avanzar 3 pasos internamente)
            self.app_s1.set_traffic_light_states(new_states=payload["data"])

            # Si hay simulación de comparación, sincronizar el avance
            if self.app_s2:
                time_s1_after = self.app_s1.traci.simulation.getTime()
                steps_advanced = time_s1_after - time_s1_before

                if steps_advanced > 0:
                    self.logger.debug(
                        f"S1 avanzó {steps_advanced:.1f} pasos por cambio de semáforos. "
                        f"Sincronizando S2..."
                    )
                    # Hacer que S2 avance los mismos pasos para mantenerse sincronizada
                    self.app_s2.advance(int(steps_advanced))

                    # Verificar sincronización final
                    if not self._check_synchronization():
                        self.logger.warning(
                            "Advertencia: Las simulaciones no quedaron perfectamente sincronizadas "
                            "después del cambio de semáforos"
                        )

            return jsonify({"estado": "OK"}), 200

        except Exception as e:
            self.logger.error(f"Error cambiando estados de semáforos: {e}")
            return jsonify({"error": f"Error interno: {str(e)}"}), 500

    def get_simulation_status(self) -> tuple[Response, int]:
        """Verificar si la simulación S1 está en ejecución."""
        return jsonify({"simulacion": self.app_s1.is_simulation_active()}), 200

    def get_report(self) -> tuple[Response, int]:
        """Reporte de flujo vehicular de S1."""
        return (
            jsonify(
                {
                    "steps": int(self.app_s1.traci.simulation.getTime()),
                    "tiempos_espera": self.app_s1.get_wait_times(),
                    "estados_semaforos": self.app_s1.get_traffic_light_states(),
                }
            ),
            200,
        )

    def reset_simulations(self) -> tuple[Response, int]:
        """Reiniciar las simulaciones S1 y S2 (si existe)."""
        try:
            # Reiniciar S1
            self.app_s1.reset()
            result = {"s1": "reiniciada"}

            # Reiniciar S2 si existe
            if self.app_s2:
                self.app_s2.reset()
                result["s2"] = "reiniciada"

            self.logger.info("🔄 Simulaciones reiniciadas exitosamente desde API")
            return (
                jsonify(
                    {
                        "mensaje": "Simulaciones reiniciadas exitosamente",
                        "resultado": result,
                    }
                ),
                200,
            )

        except Exception as e:
            self.logger.error(f"❌ Error al reiniciar simulaciones: {e}")
            return jsonify({"error": f"Error al reiniciar simulaciones: {str(e)}"}), 500
