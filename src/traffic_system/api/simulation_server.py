import logging

from flask import Flask, Response, jsonify, request

from src.traffic_system.simulation.AppSUMO import AppSUMO


class ApiSUMO(Flask):
    def __init__(
        self,
        name: str,
        app_s1: AppSUMO,
        app_s2: AppSUMO | None = None,
        comparison_logger=None,
    ) -> None:
        super().__init__(name)

        # Inyección de dependencias
        self.app_s1 = app_s1
        self.app_s2 = app_s2
        self.comparison_logger = comparison_logger

        # Logger para esta instancia
        self.logger = logging.getLogger("ApiSUMO")

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        # Las rutas no cambian
        self.route("/espera", methods=["GET"])(self.getTiemposEspera)
        self.route("/espera2", methods=["GET"])(self.getTiemposEspera2)
        self.route("/espera/<zona_id>", methods=["GET"])(self.getTiempoEspera)
        self.route("/sincronizacion", methods=["GET"])(self.getSincronizacion)
        # ... (resto de rutas sin cambios)
        self.route("/avanzar", methods=["PUT"])(self.putAvanzar)
        self.route("/semaforo", methods=["GET"])(self.getEstados)
        self.route("/semaforo", methods=["PUT"])(self.putEstados)
        self.route("/semaforo/<id>", methods=["GET"])(self.getEstado)
        self.route("/semaforo/<id>", methods=["PUT"])(self.putEstado)
        self.route("/simulacion", methods=["GET"])(self.getSimulacionOK)
        self.route("/reporte", methods=["GET"])(self.getReporte)

    def putAvanzar(self) -> tuple[Response, int]:
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
            tiempo_s1 = self.app_s1.traci.simulation.getTime()
            tiempo_s2 = self.app_s2.traci.simulation.getTime()

            # Si estamos en los primeros pasos, permitir diferencias mayores
            if (
                max(tiempo_s1, tiempo_s2) >= 5.0
                and not self._verificar_sincronizacion()
            ):
                return jsonify({"error": "Las simulaciones están desincronizadas"}), 500

        # Avanzar simulación principal (controlada por el agente)
        done_s1 = self.app_s1.avanzar(steps=steps)
        done_s2 = False

        # Si estamos en modo comparación, avanzar la segunda simulación
        # por la misma cantidad de pasos para mantenerla sincronizada.
        if self.app_s2:
            try:
                done_s2 = self.app_s2.avanzar(steps=steps)

                # Verificar que ambas simulaciones siguen sincronizadas
                # Solo mostrar warning después de los primeros pasos
                tiempo_s1_final = self.app_s1.traci.simulation.getTime()
                if tiempo_s1_final >= 5.0 and not self._verificar_sincronizacion():
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
                        if not self.app_s2 or self._verificar_sincronizacion()
                        else "desync"
                    ),
                }
            ),
            200,
        )

    def _verificar_sincronizacion(self) -> bool:
        """
        Verifica que ambas simulaciones estén sincronizadas (en el mismo paso de tiempo).
        Permite una diferencia máxima de 1 paso como se especificó.
        En los primeros pasos (t < 5s), es más permisivo para permitir la sincronización inicial.
        """
        if not self.app_s2:
            return True

        try:
            tiempo_s1 = self.app_s1.traci.simulation.getTime()
            tiempo_s2 = self.app_s2.traci.simulation.getTime()

            diferencia = abs(tiempo_s1 - tiempo_s2)

            # Ser más permisivo en los primeros pasos para permitir sincronización inicial
            if max(tiempo_s1, tiempo_s2) < 5.0:
                # En los primeros 5 segundos, permitir hasta 2 segundos de diferencia
                sincronizado = diferencia <= 2.0
                if not sincronizado:
                    self.logger.info(
                        f"Sincronización inicial: S1={tiempo_s1:.1f}s, S2={tiempo_s2:.1f}s, diff={diferencia:.1f}s (permitido en fase inicial)"
                    )
            else:
                # Después de los primeros 5 segundos, aplicar la regla normal
                sincronizado = diferencia <= 1.0
                if not sincronizado:
                    self.logger.warning(
                        f"Simulaciones desincronizadas: S1={tiempo_s1:.1f}s, S2={tiempo_s2:.1f}s, diff={diferencia:.1f}s"
                    )

            return sincronizado

        except Exception as e:
            self.logger.error(f"Error verificando sincronización: {e}")
            return False

    def getSincronizacion(self) -> tuple[Response, int]:
        """
        Endpoint para obtener información de sincronización entre las dos simulaciones.
        """
        if not self.app_s2:
            return jsonify({"error": "No hay simulación de comparación activa"}), 404

        try:
            tiempo_s1 = self.app_s1.traci.simulation.getTime()
            tiempo_s2 = self.app_s2.traci.simulation.getTime()
            diferencia = abs(tiempo_s1 - tiempo_s2)

            # Aplicar la misma lógica de sincronización que en _verificar_sincronizacion
            if max(tiempo_s1, tiempo_s2) < 5.0:
                sincronizado = diferencia <= 2.0
                max_diferencia = 2.0
                fase = "inicial"
            else:
                sincronizado = diferencia <= 1.0
                max_diferencia = 1.0
                fase = "normal"

            return (
                jsonify(
                    {
                        "sincronizado": sincronizado,
                        "tiempo_s1": tiempo_s1,
                        "tiempo_s2": tiempo_s2,
                        "diferencia": diferencia,
                        "max_diferencia_permitida": max_diferencia,
                        "fase": fase,
                    }
                ),
                200,
            )
        except Exception as e:
            self.logger.error(f"Error obteniendo sincronización: {e}")
            return jsonify({"error": str(e)}), 500

    # --- El resto de los métodos de la API no necesitan cambios ---
    # ... (getTiemposEspera, getEstados, etc. se quedan como estaban)
    def getTiemposEspera(self) -> tuple[Response, int]:
        """Obtener tiempos de espera de la simulación principal (S1)."""
        return (
            jsonify(
                {
                    "tiempo_espera_total": self.app_s1.getTiemposEsperaTotal(),
                    "tiempos_espera": self.app_s1.getTiemposEspera(),
                }
            ),
            200,
        )

    def getTiemposEspera2(self) -> tuple[Response, int]:
        """Obtener tiempos de espera de la simulación de comparación (S2)."""
        if self.app_s2 and self.app_s2.getSimulacionOK():
            return (
                jsonify(
                    {
                        "tiempo_espera_total": self.app_s2.getTiemposEsperaTotal(),
                        "tiempos_espera": self.app_s2.getTiemposEspera(),
                    }
                ),
                200,
            )
        return jsonify({"error": "Simulación de comparación no disponible."}), 404

    def getTiempoEspera(self, zona_id: str) -> tuple[Response, int]:
        """Obtener tiempo de espera de una zona en S1."""
        return (
            jsonify({"tiempo_espera": self.app_s1.getTiempoEspera(zona_id=zona_id)}),
            200,
        )

    def getEstados(self) -> tuple[Response, int]:
        """Obtener estados de semáforos de S1."""
        return jsonify({"estados": self.app_s1.getSemaforosEstados()}), 200

    def getEstado(self, id: str) -> tuple[Response, int]:
        """Obtener estado de un semáforo de S1."""
        return jsonify({"estado": self.app_s1.getSemaforoEstado(id)}), 200

    def putEstado(self, id) -> tuple[Response, int]:
        """Cambiar el estado de un semáforo en S1."""
        estado = request.args.get("estado", type=str)
        if estado:
            self.app_s1.setSemaforoEstado(id, estado)
            return jsonify({"estado": estado}), 200
        return jsonify({"error": "Falta el parámetro 'estado'."}), 400

    def putEstados(self) -> tuple[Response, int]:
        """Cambiar los estados de varios semáforos en S1."""
        data = request.json
        if data and "data" in data:
            self.app_s1.setSemaforosEstados(estados_nuevos=data["data"])
            return jsonify({"estado": "OK"}), 200
        return jsonify({"error": "Falta el campo 'data' en el JSON."}), 400

    def getSimulacionOK(self) -> tuple[Response, int]:
        """Verificar si la simulación S1 está en ejecución."""
        return jsonify({"simulacion": self.app_s1.getSimulacionOK()}), 200

    def getReporte(self) -> tuple[Response, int]:
        """Reporte de flujo vehicular de S1."""
        return (
            jsonify(
                {
                    "steps": int(self.app_s1.traci.simulation.getTime()),
                    "tiempos_espera": self.app_s1.getTiemposEspera(),
                    "estados_semaforos": self.app_s1.getSemaforosEstados(),
                }
            ),
            200,
        )
