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

        #! Cantidades
        self.route("/cantidad", methods=["GET"])(self.get_all_quantities)
        self.route("/cantidad/<zone_name>", methods=["GET"])(self.get_zone_quantity)

        #! Tiempos
        self.route("/espera", methods=["GET"])(self.get_wait_times)

        #! Multas
        self.route("/multas/<zone_name>", methods=["POST"])(self.activate_fines)

    def get_all_quantities(self) -> tuple[Response, int]:
        """
        Cantidades de vehículos por cada una de las zonas.
        """
        quantities = self.zones.get_all_quantities()
        response = VehicleQuantitiesResponse(
            cantidades=quantities,
            total_vehicles=sum(quantities.values()),
        )
        return jsonify(response.model_dump()), 200

    def get_zone_quantity(self, zone_name: str) -> tuple[Response, int]:
        """
        Cantidad de vehículos en una zona específica.
        """
        quantity = self.zones.get_zone_quantity(zone_name)
        response = VehicleQuantitiesResponse(
            cantidades={zone_name: quantity},
            total_vehicles=quantity,
        )
        return jsonify(response.model_dump()), 200

    def get_wait_times(self) -> tuple[Response, int]:
        """
        Devuelve los tiempos de espera en cada zona.

        Return:
            WaitTimesResponse: Respuesta tipada con tiempos de espera
        """
        wait_times_raw = self.zones.get_zone_wait_times()
        wait_times = [float(wt) for wt in wait_times_raw]  # Convertir a float
        total_wait_time = float(self.zones.get_total_wait_time())

        response = WaitTimesResponse(
            tiempos_espera=wait_times,
            tiempo_espera_total=total_wait_time,
            promedio_espera=sum(wait_times) / len(wait_times) if wait_times else 0.0,
        )

        return jsonify(response.model_dump()), 200

    def activate_fines(self, zone_name: str) -> tuple[Response, int]:
        """
        Activa las multas en las zonas.
        """
        result = self.zones.activate_fines(zone_name)
        response = SuccessResponse(message=f"Multas {zone_name}: {result}")

        return jsonify(response.model_dump()), 200
