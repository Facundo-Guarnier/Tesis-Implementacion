import logging
from collections.abc import Callable
from typing import Any

from flask import Flask, Response, jsonify, request

from src.traffic_system.core.api_models import (
    ErrorResponse,
    ReportResponse,
    SimulationStatusResponse,
    SimulationStepResponse,
    SuccessResponse,
    SynchronizationResponse,
    TrafficLightStateResponse,
    TrafficLightStatesResponse,
    VehicleQuantitiesResponse,
    WaitTimesResponse,
)

# from src.traffic_system.core.smart_logger import (
#     SIMULATION_LOGGER_CONFIG,
#     create_smart_logger,
# )
from src.traffic_system.simulation.app import SumoApp

# Constants for simulation defaults when done
DEFAULT_SIMULATION_TIME = 0.0
DEFAULT_VEHICLES_COUNT = 0


class SumoAPI(Flask):
    def __init__(
        self,
        name: str,
        app_s1: SumoApp,
        app_s2: SumoApp | None = None,
        comparison_logger: Any = None,
        seed_info_callback: Callable | None = None,
    ) -> None:
        super().__init__(name)

        self.app_s1 = app_s1
        self.app_s2 = app_s2
        self.comparison_logger = comparison_logger
        self.seed_info_callback = seed_info_callback

        # CONFIGURAR SMART LOGGING para evitar spam
        # self.smart_logger = create_smart_logger("SumoAPI", SIMULATION_LOGGER_CONFIG)
        self.sumo_logger = logging.getLogger("SumoAPI")

        # Estado interno para rastrear si alguna operación de semáforos terminó la simulación
        self._simulation_ended_during_traffic_light_change = False

        # Logging detallado de requests para debuggear MemoryError
        self.before_request(self._log_request_details)

        # Handler global para MemoryError con información completa
        self.register_error_handler(MemoryError, self._handle_memory_error_with_debug)

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        self.route("/espera", methods=["GET"])(self.get_wait_times)
        self.route("/espera2", methods=["GET"])(self.get_wait_times_s2)
        self.route("/espera/<zone_id>", methods=["GET"])(self.get_zone_wait_time)
        self.route("/cantidad", methods=["GET"])(self.get_vehicle_quantities)
        self.route("/cantidad/<zone_id>", methods=["GET"])(
            self.get_zone_vehicle_quantity
        )
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
            error_response = ErrorResponse(error="Falta el parámetro 'steps'.")
            return jsonify(error_response.model_dump()), 400

        # VERIFICAR PRIMERO si la simulación terminó en una operación anterior de semáforos
        if self._simulation_ended_during_traffic_light_change:
            self.sumo_logger.info(
                "🏁 step_simulation: Detectada terminación previa durante cambio de semáforos. "
                "Devolviendo done=True (simulaciones ya reiniciadas)."
            )
            # Limpiar el flag y devolver done=True
            self._simulation_ended_during_traffic_light_change = False

            # Obtener información de semilla si hay callback disponible
            seed_info = None
            if self.seed_info_callback:
                try:
                    seed_info = self.seed_info_callback()
                except Exception as e:
                    self.sumo_logger.warning(
                        f"Error obteniendo información de semilla: {e}"
                    )

            response = SimulationStepResponse(
                done=True,
                current_time=DEFAULT_SIMULATION_TIME,
                vehicles_count=DEFAULT_VEHICLES_COUNT,
                info=seed_info,
            )
            return jsonify(response.model_dump()), 200

        # Verificar estado inicial de ambas simulaciones
        # Solo aplicar verificación estricta después de los primeros pasos
        if self.app_s2:
            time_s1 = self.app_s1.traci.simulation.getTime()
            time_s2 = self.app_s2.traci.simulation.getTime()

            # Si estamos en los primeros pasos, permitir diferencias mayores
            if max(time_s1, time_s2) >= 5.0 and not self._check_synchronization():
                error_response = ErrorResponse(
                    error="Las simulaciones están desincronizadas"
                )
                return jsonify(error_response.model_dump()), 500

        # Capturar TODOS los estados ANTES de cualquier operación
        time_s1_before = self.app_s1.traci.simulation.getTime()
        vehicles_s1_before = len(self.app_s1.traci.vehicle.getIDList())

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
                if (
                    tiempo_s1_final >= 5.0
                    and not done_s1
                    and not done_s2
                    and not self._check_synchronization()
                ):
                    self.sumo_logger.warning(
                        "Las simulaciones se desincronizaron durante el avance"
                    )

            except Exception as e:
                self.sumo_logger.error(
                    f"Error avanzando simulación de comparación: {e}"
                )
                error_response = ErrorResponse(
                    error=f"Error en simulación de comparación: {str(e)}"
                )
                return jsonify(error_response.model_dump()), 500

        # La simulación se considera terminada si cualquiera de las dos termina
        done = done_s1 or done_s2

        # Si alguna simulación terminó, reiniciarlas DESPUÉS de capturar el estado
        if done:
            # Mostrar resumen final de métricas comparativas antes de reiniciar
            if self.comparison_logger and self.app_s2:
                self.comparison_logger.log_final_comparative_summary()

            # Reiniciar S1
            if done_s1:
                self.app_s1.reset()

            # Reiniciar S2 si existe y terminó
            if self.app_s2 and done_s2:
                self.app_s2.reset()

            # Si solo una terminó, reiniciar ambas para mantener sincronización
            elif self.app_s2 and done:
                if not done_s1:
                    self.app_s1.reset()
                if not done_s2:
                    self.app_s2.reset()

        # Si hay un logger de comparación, invocarlo para que verifique
        # si debe registrar las métricas (solo si no se reiniciaron las simulaciones)
        if self.comparison_logger and self.app_s2 and not done:
            self.comparison_logger.log_if_needed(self.app_s1, self.app_s2)

        # Obtener información de semilla SIEMPRE si hay callback disponible
        seed_info = None
        if self.seed_info_callback:
            try:
                seed_info = self.seed_info_callback()
            except Exception as e:
                self.sumo_logger.warning(
                    f"Error obteniendo información de semilla: {e}"
                )

        # Crear respuesta tipada usando SIEMPRE los estados capturados ANTES de advance()
        # Esto garantiza consistencia independientemente de reinicios
        if done:
            # Reportar tiempo 0 cuando done=True para consistencia con logs esperados

            response = SimulationStepResponse(
                done=True,  # Usar valor determinado, no verificar estado actual
                current_time=DEFAULT_SIMULATION_TIME,
                vehicles_count=DEFAULT_VEHICLES_COUNT,
                info=seed_info,
            )
        else:
            # Usar SIEMPRE los estados capturados antes de advance() para evitar race conditions
            # Pero actualizarlos con el avance real que se hizo
            steps_advanced = steps  # El número de pasos solicitados
            estimated_time_after = time_s1_before + steps_advanced

            # Solo si no hay problemas, usar el tiempo real actual
            try:
                actual_time_after = self.app_s1.traci.simulation.getTime()
                actual_vehicles_after = len(self.app_s1.traci.vehicle.getIDList())

                # Verificación de consistencia: si hay gran diferencia, usar estimado
                time_diff = abs(actual_time_after - estimated_time_after)
                if time_diff > 50:  # Diferencia sospechosa
                    self.sumo_logger.warning(
                        f"⚠️ Diferencia temporal sospechosa: estimated={estimated_time_after:.1f}s, "
                        f"actual={actual_time_after:.1f}s, diff={time_diff:.1f}s"
                    )
                    # Usar valores seguros
                    final_time = estimated_time_after
                    final_vehicles = vehicles_s1_before
                else:
                    final_time = actual_time_after
                    final_vehicles = actual_vehicles_after

            except Exception as e:
                self.sumo_logger.error(f"Error leyendo estado post-advance: {e}")
                # Fallback a estimación
                final_time = estimated_time_after
                final_vehicles = vehicles_s1_before

            response = SimulationStepResponse(
                done=False,  # Usar valor determinado, no verificar estado actual
                current_time=final_time,
                vehicles_count=final_vehicles,
                info=seed_info,
            )

        return jsonify(response.model_dump()), 200

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
                    self.sumo_logger.info(
                        f"Sincronización inicial: S1={time_s1 :.1f}s, S2={time_s2:.1f}s, diff={difference :.1f}s (permitido en fase inicial)"
                    )
            else:
                # Después de los primeros 5 segundos, aplicar la regla normal
                is_synced = difference <= 1.0
                if not is_synced:
                    self.sumo_logger.warning(
                        f"Simulaciones desincronizadas: S1={time_s1 :.1f}s, S2={time_s2:.1f}s, diff={difference :.1f}s"
                    )

            return is_synced

        except Exception as e:
            self.sumo_logger.error(f"Error verificando sincronización: {e}")
            return False

    def get_synchronization_status(self) -> tuple[Response, int]:
        """
        Endpoint para obtener información de sincronización entre las dos simulaciones.
        """
        if not self.app_s2:
            try:
                time_s1: float = self.app_s1.traci.simulation.getTime()
            except Exception:
                time_s1 = 0.0

            response = SynchronizationResponse(
                sincronizado=True,
                diferencia_tiempo=0.0,
                s1_time=time_s1,
                s2_time=None,
                tolerancia=None,
            )
            return jsonify(response.model_dump()), 200

        try:
            time_s1 = self.app_s1.traci.simulation.getTime()
            time_s2: float = self.app_s2.traci.simulation.getTime()
            difference: float = abs(time_s1 - time_s2)

            if max(time_s1, time_s2) < 5.0:
                is_synced = difference <= 2.0
                max_allowed_difference = 2.0
            else:
                is_synced = difference <= 1.0
                max_allowed_difference = 1.0

            response = SynchronizationResponse(
                sincronizado=is_synced,
                diferencia_tiempo=difference,
                s1_time=time_s1,
                s2_time=time_s2,
                tolerancia=max_allowed_difference,
            )

            return jsonify(response.model_dump()), 200
        except Exception as e:
            self.sumo_logger.error(f"Error obteniendo sincronización: {e}")
            error_response = ErrorResponse(error=str(e))
            return jsonify(error_response.model_dump()), 500

    # --- El resto de los métodos de la API no necesitan cambios ---
    # ... (getTiemposEspera, getEstados, etc. se quedan como estaban)
    def get_wait_times(self) -> tuple[Response, int]:
        """Obtener tiempos de espera de la simulación principal (S1)."""
        wait_times = self.app_s1.get_wait_times()
        total_wait_time = self.app_s1.get_total_wait_time()

        response = WaitTimesResponse(
            tiempos_espera=wait_times,
            tiempo_espera_total=total_wait_time,
            promedio_espera=sum(wait_times) / len(wait_times) if wait_times else 0.0,
        )

        return jsonify(response.model_dump()), 200

    def get_wait_times_s2(self) -> tuple[Response, int]:
        """Obtener tiempos de espera de la simulación de comparación (S2)."""
        if self.app_s2 and self.app_s2.is_simulation_active():
            wait_times = self.app_s2.get_wait_times()
            total_wait_time = self.app_s2.get_total_wait_time()

            response = WaitTimesResponse(
                tiempos_espera=wait_times,
                tiempo_espera_total=total_wait_time,
                promedio_espera=(
                    sum(wait_times) / len(wait_times) if wait_times else 0.0
                ),
            )

            return jsonify(response.model_dump()), 200

        error_response = ErrorResponse(error="Simulación de comparación no disponible.")
        return jsonify(error_response.model_dump()), 404

    def get_zone_wait_time(self, zone_id: str) -> tuple[Response, int]:
        """Obtener tiempo de espera de una zona en S1."""
        return (
            jsonify({"tiempo_espera": self.app_s1.get_zone_wait_time(zone_id=zone_id)}),
            200,
        )

    def get_vehicle_quantities(self) -> tuple[Response, int]:
        """Obtener cantidades de vehículos de todas las zonas en S1."""
        vehicle_counts = self.app_s1.get_vehicle_counts_by_zone()
        total_vehicles = self.app_s1.get_vehicle_count()

        response = VehicleQuantitiesResponse(
            cantidades=vehicle_counts,
            total_vehicles=total_vehicles,
        )

        return jsonify(response.model_dump()), 200

    def get_zone_vehicle_quantity(self, zone_id: str) -> tuple[Response, int]:
        """Obtener cantidad de vehículos de una zona específica en S1."""
        try:
            zone_count = self.app_s1.get_zone_vehicle_count(zone_id)

            response = VehicleQuantitiesResponse(
                cantidades={zone_id: zone_count},
                total_vehicles=zone_count,
            )

            return jsonify(response.model_dump()), 200
        except Exception as e:
            self.sumo_logger.error(
                f"❌ Error obteniendo cantidad de vehículos para zona {zone_id}: {e}"
            )
            error_response = ErrorResponse(
                error=f"Error obteniendo cantidad de vehículos para zona {zone_id}"
            )
            return jsonify(error_response.model_dump()), 500

    def get_all_traffic_light_states(self) -> tuple[Response, int]:
        """Obtener estados de semáforos de S1."""
        states_list = self.app_s1.get_traffic_light_states()
        # Convertir lista a diccionario con IDs
        states_dict = {str(i + 1): state for i, state in enumerate(states_list)}

        response = TrafficLightStatesResponse(
            estados=states_dict,
            total_lights=len(states_dict),
        )
        return jsonify(response.model_dump()), 200

    def get_traffic_light_state(self, id: str) -> tuple[Response, int]:
        """Obtener estado de un semáforo de S1."""
        state = self.app_s1.get_traffic_light_state(id)
        response = TrafficLightStateResponse(
            estado=state,
            light_id=id,
        )
        return jsonify(response.model_dump()), 200

    def set_traffic_light_state(self, light_id: str) -> tuple[Response, int]:
        """Cambiar el estado de un semáforo en S1."""
        state = request.args.get("estado", type=str)
        if not state:
            error_response = ErrorResponse(error="Falta el parámetro 'estado'.")
            return jsonify(error_response.model_dump()), 400

        try:
            # Capturar tiempo antes del cambio
            time_s1_before = self.app_s1.traci.simulation.getTime()

            # Cambiar estado del semáforo en S1 (esto puede avanzar 3 pasos internamente)
            done_s1 = self.app_s1.set_traffic_light_state(light_id, state)

            # Si la simulación terminó durante el cambio, REINICIAR INMEDIATAMENTE
            # y marcar el flag para que step_simulation lo reporte en la próxima llamada
            if done_s1:
                self.sumo_logger.info(
                    f"🏁 Simulación terminó durante cambio de semáforo {light_id}. "
                    f"Reiniciando inmediatamente y marcando flag."
                )

                # Reiniciar S1 inmediatamente
                self.app_s1.reset()

                # Reiniciar S2 si existe
                if self.app_s2:
                    self.app_s2.reset()

                # Marcar flag para que step_simulation reporte done=True
                self._simulation_ended_during_traffic_light_change = True

            # Si hay simulación de comparación, sincronizar el avance SOLO si no terminó
            elif self.app_s2:
                time_s1_after = self.app_s1.traci.simulation.getTime()
                steps_advanced = time_s1_after - time_s1_before

                if steps_advanced > 0:
                    # Hacer que S2 avance los mismos pasos para mantenerse sincronizada
                    done_s2 = self.app_s2.advance(int(steps_advanced))
                    if done_s2:
                        self.sumo_logger.info(
                            "🏁 S2 terminó durante sincronización de semáforo. "
                            "Reiniciando inmediatamente y marcando flag."
                        )

                        # Reiniciar ambas inmediatamente
                        self.app_s1.reset()
                        self.app_s2.reset()

                        # Marcar flag para que step_simulation reporte done=True
                        self._simulation_ended_during_traffic_light_change = True

            response = TrafficLightStateResponse(
                estado=state,
                light_id=light_id,
            )
            return jsonify(response.model_dump()), 200

        except Exception as e:
            self.sumo_logger.error(
                f"Error cambiando estado de semáforo {light_id}: {e}"
            )
            error_response = ErrorResponse(error=f"Error interno: {str(e)}")
            return jsonify(error_response.model_dump()), 500

    def set_all_traffic_light_states(self) -> tuple[Response, int]:
        """Cambiar los estados de varios semáforos en S1."""
        payload = request.json
        if not payload or "data" not in payload:
            error_response = ErrorResponse(error="Falta el campo 'data' en el JSON.")
            return jsonify(error_response.model_dump()), 400

        try:
            # Capturar tiempo antes del cambio
            time_s1_before = self.app_s1.traci.simulation.getTime()

            # Cambiar estados de semáforos en S1 (esto puede avanzar 3 pasos internamente)
            done_s1 = self.app_s1.set_traffic_light_states(new_states=payload["data"])

            # Si la simulación terminó durante el cambio, REINICIAR INMEDIATAMENTE
            # y marcar el flag para que step_simulation lo reporte en la próxima llamada
            if done_s1:
                self.sumo_logger.info(
                    "🏁 Simulación terminó durante cambio de semáforos. "
                    "Reiniciando inmediatamente y marcando flag."
                )

                # Reiniciar S1 inmediatamente
                self.app_s1.reset()

                # Reiniciar S2 si existe
                if self.app_s2:
                    self.app_s2.reset()

                # Marcar flag para que step_simulation reporte done=True
                self._simulation_ended_during_traffic_light_change = True

            # Si hay simulación de comparación, sincronizar el avance SOLO si no terminó
            elif self.app_s2:
                time_s1_after = self.app_s1.traci.simulation.getTime()
                steps_advanced = time_s1_after - time_s1_before

                if steps_advanced > 0:
                    # Hacer que S2 avance los mismos pasos para mantenerse sincronizada
                    done_s2 = self.app_s2.advance(int(steps_advanced))
                    if done_s2:
                        self.sumo_logger.info(
                            "🏁 S2 terminó durante sincronización de semáforos. "
                            "Reiniciando inmediatamente y marcando flag."
                        )

                        # Reiniciar ambas inmediatamente
                        self.app_s1.reset()
                        self.app_s2.reset()

                        # Marcar flag para que step_simulation reporte done=True
                        self._simulation_ended_during_traffic_light_change = True

            response = SuccessResponse(
                message="Estados de semáforos actualizados correctamente"
            )
            return jsonify(response.model_dump()), 200

        except Exception as e:
            self.sumo_logger.error(f"Error cambiando estados de semáforos: {e}")
            error_response = ErrorResponse(error=f"Error interno: {str(e)}")
            return jsonify(error_response.model_dump()), 500

    def get_simulation_status(self) -> tuple[Response, int]:
        """Verificar si la simulación S1 está en ejecución."""
        response = SimulationStatusResponse(
            simulacion=self.app_s1.is_simulation_active(),
            tiempo_actual=(
                self.app_s1.traci.simulation.getTime()
                if self.app_s1.is_simulation_active()
                else None
            ),
            modo_comparacion=self.app_s2 is not None,
        )
        return jsonify(response.model_dump()), 200

    def get_report(self) -> tuple[Response, int]:
        """Reporte de flujo vehicular de S1."""
        # "steps": int(self.app_s1.traci.simulation.getTime()),  # int
        # "tiempos_espera": self.app_s1.get_wait_times(),  # list[float]
        # "cantidad_vehiculos_por_zona": self.app_s1.get_vehicle_counts_by_zone(),  # dict[str, int]
        # "estados_semaforos": self.app_s1.get_traffic_light_states(),  # list[str]

        response = ReportResponse(
            steps=int(self.app_s1.traci.simulation.getTime()),
            tiempos_espera=self.app_s1.get_wait_times(),
            cantidad_vehiculos_por_zona=self.app_s1.get_vehicle_counts_by_zone(),
            estados_semaforos=self.app_s1.get_traffic_light_states(),
            generated_at=f"{int(self.app_s1.traci.simulation.getTime())}s",
        )
        return jsonify(response.model_dump()), 200

    def reset_simulations(self) -> tuple[Response, int]:
        """Reiniciar las simulaciones S1 y S2 (si existe)."""
        try:
            # Limpiar el flag de terminación durante cambio de semáforos
            self._simulation_ended_during_traffic_light_change = False

            # Reiniciar S1
            self.app_s1.reset()
            result = {"s1": "reiniciada"}

            # Reiniciar S2 si existe
            if self.app_s2:
                self.app_s2.reset()
                result["s2"] = "reiniciada"

            self.sumo_logger.info("🔄 Simulaciones reiniciadas exitosamente desde API")
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
            self.sumo_logger.error(f"❌ Error al reiniciar simulaciones: {e}")
            error_response = ErrorResponse(
                error=f"Error al reiniciar simulaciones: {str(e)}"
            )
            return jsonify(error_response.model_dump()), 500

    def _log_request_details(self) -> None:
        """Loggea detalles de todas las requests entrantes para debuggear."""
        import datetime

        from flask import request

        # Información básica de la request
        content_length = request.content_length or 0

        method = request.method
        url = request.url
        headers = dict(request.headers)

        # Log básico siempre

        # Si la request es sospechosamente grande, loggear más detalles
        if content_length > 1_000:  # 1 KB
            self.sumo_logger.info(
                f"📥 Request: {method} {url} | Size: {content_length:,} bytes"
            )
            self.sumo_logger.warning(
                f"⚠️  REQUEST GRANDE DETECTADA: {content_length:,} bytes"
            )
            self.sumo_logger.warning(f"Headers: {headers}")

            # Guardar request grande en archivo para análisis
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debug_large_request_{timestamp}.json"

            try:
                debug_data = {
                    "timestamp": timestamp,
                    "method": method,
                    "url": url,
                    "content_length": content_length,
                    "headers": headers,
                    "args": dict(request.args),
                    "form": dict(request.form) if request.form else None,
                }

                # Intentar capturar el JSON si es posible
                try:
                    if request.is_json:
                        debug_data["json_data"] = request.get_json()
                except Exception as e:
                    debug_data["json_error"] = str(e)

                import json

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(debug_data, f, indent=2, ensure_ascii=False)

                self.sumo_logger.warning(f"💾 Request guardada en: {filename}")

            except Exception as e:
                self.sumo_logger.error(f"❌ Error guardando request debug: {e}")

    def _handle_memory_error_with_debug(
        self, error: MemoryError
    ) -> tuple[Response, int]:
        """Handler para MemoryError con información completa de debug."""
        import datetime
        import json
        import traceback

        from flask import request

        self.sumo_logger.error(f"💥 MEMORY ERROR DETECTADO: {error}")

        # Capturar toda la información posible
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        debug_info: dict[str, Any] = {
            "timestamp": timestamp,
            "error": str(error),
            "traceback": traceback.format_exc(),
            "request_info": {
                "method": getattr(request, "method", "UNKNOWN"),
                "url": getattr(request, "url", "UNKNOWN"),
                "content_length": getattr(request, "content_length", 0),
                "headers": dict(getattr(request, "headers", {})),
                "remote_addr": getattr(request, "remote_addr", "UNKNOWN"),
            },
        }

        # Guardar información de debug
        debug_filename = f"MEMORY_ERROR_DEBUG_{timestamp}.json"
        try:

            with open(debug_filename, "w", encoding="utf-8") as f:
                json.dump(debug_info, f, indent=2, ensure_ascii=False)

            self.sumo_logger.error(f"🔍 Debug info guardada en: {debug_filename}")
        except Exception as save_error:
            self.sumo_logger.error(f"❌ Error guardando debug info: {save_error}")

        # Log completo en consola
        self.sumo_logger.error("=" * 80)
        self.sumo_logger.error("MEMORY ERROR COMPLETO:")

        # Extraer información del request con type hints claros
        request_info: dict[str, Any] = debug_info["request_info"]
        method = request_info.get("method", "UNKNOWN")
        url = request_info.get("url", "UNKNOWN")
        content_length = request_info.get("content_length", 0)
        headers = dict(request_info.get("headers", {}))
        traceback_str = debug_info.get("traceback", "")

        self.sumo_logger.error(f"Request: {method} {url}")
        self.sumo_logger.error(f"Content-Length: {content_length:,} bytes")
        self.sumo_logger.error(f"Headers: {headers}")
        self.sumo_logger.error(f"Traceback: {traceback_str}")
        self.sumo_logger.error("=" * 80)

        # Fallar intencionalmente para que el desarrollador vea el problema
        raise error

    def _handle_payload_too_large(self, error: Exception) -> tuple[Response, int]:
        """Handler para payloads demasiado grandes."""
        self.sumo_logger.error(f"❌ Payload demasiado grande: {error}")

        error_response = ErrorResponse(
            error="Request demasiado grande. Máximo permitido: 1MB"
        )
        return jsonify(error_response.model_dump()), 413
