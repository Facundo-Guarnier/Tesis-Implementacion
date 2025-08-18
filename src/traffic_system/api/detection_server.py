import logging

from flask import Flask, Response, jsonify

from src.traffic_system.core.api_models import (
    SuccessResponse,
    VehicleQuantitiesResponse,
    WaitTimesResponse,
)
from src.traffic_system.detection.zones.zone_list import ZoneList


class DetectionAPI(Flask):
    """
    La "lógica o toma de decisiones" consultará a la API para saber la cantidad de
    vehículos que hay en cada zona.
    """

    def __init__(self, name: str, instance_zones: ZoneList | None = None) -> None:
        super().__init__(name)

        self.zones = instance_zones if instance_zones is not None else ZoneList()
        self.detection_logger = logging.getLogger(f"{self.__class__.__name__}[{name}]")

        #! Cantidades
        self.route("/cantidad", methods=["GET"])(self.get_all_quantities)
        self.route("/cantidad/<zone_name>", methods=["GET"])(self.get_zone_quantity)

        #! Tiempos
        self.route("/espera", methods=["GET"])(self.get_wait_times)
        self.route("/espera/<zone_name>", methods=["GET"])(self.get_zone_wait_time)

        #! Multas
        self.route("/multas/<zone_name>", methods=["POST"])(self.activate_fines)

    def get_all_quantities(self) -> tuple[Response, int]:
        """
        Cantidades de vehículos por cada una de las zonas.
        """
        try:
            quantities = self.zones.get_all_quantities()
            response = VehicleQuantitiesResponse(
                cantidades=quantities,
                total_vehicles=sum(quantities.values()),
            )
            self.detection_logger.info(f"📊 Cantidades obtenidas: {quantities}")
            return jsonify(response.model_dump()), 200
        except Exception:
            self.detection_logger.error(
                "❌ Error obteniendo cantidades de vehículos", exc_info=True
            )
            return jsonify({"error": "Error interno del servidor"}), 500

    def get_zone_quantity(self, zone_name: str) -> tuple[Response, int]:
        """
        Cantidad de vehículos en una zona específica.
        """
        try:
            quantity = self.zones.get_zone_quantity(zone_name)
            if quantity == -1:
                self.detection_logger.warning(f"⚠️ Zona no encontrada: {zone_name}")
                return jsonify({"error": f"Zona '{zone_name}' no encontrada"}), 404

            response = VehicleQuantitiesResponse(
                cantidades={zone_name: quantity},
                total_vehicles=quantity,
            )
            self.detection_logger.info(f"🎯 Cantidad zona {zone_name}: {quantity}")
            return jsonify(response.model_dump()), 200
        except Exception:
            self.detection_logger.error(
                f"❌ Error obteniendo cantidad para zona {zone_name}", exc_info=True
            )
            return jsonify({"error": "Error interno del servidor"}), 500

    def get_zone_wait_time(self, zone_name: str) -> tuple[Response, int]:
        """
        Tiempo de espera en una zona específica.
        """
        try:
            # Obtener el índice de la zona
            zone_index = None
            for i, zone in enumerate(self.zones.get_all_zones()):
                if zone.name == zone_name:
                    zone_index = i
                    break

            if zone_index is None:
                self.detection_logger.warning(f"⚠️ Zona no encontrada: {zone_name}")
                return jsonify({"error": f"Zona '{zone_name}' no encontrada"}), 404

            # Obtener tiempo de espera para esa zona específica
            wait_times_raw = self.zones.get_zone_wait_times()
            if zone_index >= len(wait_times_raw):
                self.detection_logger.warning(
                    f"⚠️ Índice de zona fuera de rango: {zone_name}"
                )
                return (
                    jsonify({"error": f"Datos no disponibles para zona '{zone_name}'"}),
                    404,
                )

            zone_wait_time = float(wait_times_raw[zone_index])

            response = WaitTimesResponse(
                tiempos_espera=[zone_wait_time],
                tiempo_espera_total=zone_wait_time,
                promedio_espera=zone_wait_time,
            )

            self.detection_logger.info(
                f"⏱️ Tiempo espera zona {zone_name}: {zone_wait_time:.2f}s"
            )
            return jsonify(response.model_dump()), 200
        except Exception:
            self.detection_logger.error(
                f"❌ Error obteniendo tiempo de espera para zona {zone_name}",
                exc_info=True,
            )
            return jsonify({"error": "Error interno del servidor"}), 500

    def get_wait_times(self) -> tuple[Response, int]:
        """
        Devuelve los tiempos de espera en cada zona.

        Return:
            WaitTimesResponse: Respuesta tipada con tiempos de espera
        """
        try:
            wait_times_raw = self.zones.get_zone_wait_times()
            wait_times = [float(wt) for wt in wait_times_raw]  # Convertir a float
            total_wait_time = float(self.zones.get_total_wait_time())

            response = WaitTimesResponse(
                tiempos_espera=wait_times,
                tiempo_espera_total=total_wait_time,
                promedio_espera=(
                    sum(wait_times) / len(wait_times) if wait_times else 0.0
                ),
            )

            self.detection_logger.info(
                f"⏱️ Tiempos de espera obtenidos: {total_wait_time:.2f}s total"
            )
            return jsonify(response.model_dump()), 200
        except Exception:
            self.detection_logger.error(
                "❌ Error obteniendo tiempos de espera", exc_info=True
            )
            return jsonify({"error": "Error interno del servidor"}), 500

    def activate_fines(self, zone_name: str) -> tuple[Response, int]:
        """
        Activa las multas en las zonas.
        """
        try:
            result = self.zones.activate_fines(zone_name)
            status = "activadas" if result else "desactivadas"
            message = f"Multas {zone_name}: {status}"

            self.detection_logger.info(f"🚨 {message}")
            response = SuccessResponse(message=message)
            return jsonify(response.model_dump()), 200
        except Exception:
            self.detection_logger.error(
                f"❌ Error activando multas para zona {zone_name}", exc_info=True
            )
            return jsonify({"error": "Error interno del servidor"}), 500
