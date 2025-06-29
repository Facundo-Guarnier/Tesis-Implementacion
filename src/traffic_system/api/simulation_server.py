# src\traffic_system\api\simulation_server.py

import logging

from flask import Flask, Response, jsonify, request

# Asumimos que AppSUMO está en este namespace relativo al iniciar desde la raíz
from src.traffic_system.simulation.AppSUMO import AppSUMO


class ApiSUMO(Flask):
    def __init__(
        self, name: str, app_s1: AppSUMO, app_s2: AppSUMO | None = None
    ) -> None:
        super().__init__(name)

        # Inyección de dependencias
        self.app_s1 = app_s1
        self.app_s2 = app_s2

        #! Configurar el logger de Flask para evitar imprimir registros de acceso
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        # Rutas (sin cambios en las URLs)
        self.route("/espera", methods=["GET"])(self.getTiemposEspera)  # S1
        self.route("/espera2", methods=["GET"])(self.getTiemposEspera2)  # S2
        self.route("/espera/<zona_id>", methods=["GET"])(self.getTiempoEspera)

        self.route("/avanzar", methods=["PUT"])(self.putAvanzar)

        self.route("/semaforo", methods=["GET"])(self.getEstados)
        self.route("/semaforo", methods=["PUT"])(self.putEstados)
        self.route("/semaforo/<id>", methods=["GET"])(self.getEstado)
        self.route("/semaforo/<id>", methods=["PUT"])(self.putEstado)

        #! Simulación ok
        self.route("/simulacion", methods=["GET"])(self.getSimulacionOK)

        #! Reporte de flujo vehicular
        self.route("/reporte", methods=["GET"])(self.getReporte)

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

    def putAvanzar(self) -> tuple[Response, int]:
        """Avanzar la simulación S1."""
        steps = request.args.get("steps", type=int)
        if steps:
            done = self.app_s1.avanzar(steps=steps)
            return jsonify({"done": done}), 200
        return jsonify({"error": "Falta el parámetro 'steps'."}), 400

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
