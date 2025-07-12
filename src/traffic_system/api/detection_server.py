from flask import Flask, Response, jsonify

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
        self.route("/cantidad/<zona_name>", methods=["GET"])(self.get_zone_quantity)

        #! Tiempos
        self.route("/espera", methods=["GET"])(self.get_wait_times)

        #! Multas
        self.route("/multas/<zona_name>", methods=["POST"])(self.activate_fines)

    def get_all_quantities(self) -> tuple[Response, int]:
        """
        Cantidades de vehículos por cada una de las zonas.
        """
        return jsonify(self.zones.get_all_quantities()), 200

    def get_zone_quantity(self, zona_name: str) -> tuple[Response, int]:
        """
        Cantidad de vehículos en una zona específica.
        """
        return (
            jsonify(
                {
                    "zona": zona_name,
                    "cantidad_detecciones": self.zones.get_zone_quantity(zona_name),
                }
            ),
            200,
        )

    def get_wait_times(self) -> tuple[Response, int]:
        """
        Devuelve los tiempos de espera en cada zona.

        Return:
            - dict -> {"tiempo_espera_total": int, "tiempos_espera": list[int]}
        """
        return (
            jsonify(
                {
                    "tiempo_espera_total": self.zones.get_total_wait_time(),
                    "tiempos_espera": self.zones.get_zone_wait_times(),
                }
            ),
            200,
        )

    def activate_fines(self, zona_name: str) -> tuple[Response, int]:
        """
        Activa las multas en las zonas.
        """

        return (
            jsonify(
                {
                    "mensaje": f"Multas {zona_name}: {self.zones.activate_fines(zona_name)}"
                }
            ),
            200,
        )
