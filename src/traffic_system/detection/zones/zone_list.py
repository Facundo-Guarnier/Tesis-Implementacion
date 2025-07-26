from __future__ import annotations

import numpy as np
import yaml

from src.traffic_system.detection.zones.zone import Zone


class ZoneList:
    """
    Clase de tipo "Singleton" que:
    - Se encarga de cargar las zonas desde un archivo YAML.
    - Representa una lista de zonas (List[Zona]).
    """

    _instance: ZoneList | None = None

    def __new__(cls) -> ZoneList:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.zones = self._load_zones()

    def _load_zones(self) -> list[Zone]:
        # TODO: Cambiar la ruta por una ruta relativa en config.yaml
        with open("assets/detection_zones/zones.yaml", encoding="utf-8") as file:
            yaml_data = yaml.safe_load(file)
            return [
                Zone(
                    name=zone["Nombre"],
                    resolution=tuple(zone["Resolucion"]),
                    original_points=np.array(zone["Puntos"]),
                    original_fine_points=np.array(zone["Multa"]),
                )
                for zone in yaml_data["Zonas"]
            ]

    def get_all_quantities(self) -> dict:
        """
        Cantidades de vehículos por cada una de las zonas.
        """
        quantities = {}
        for zone in self.zones:
            quantities[zone.name] = zone.detection_count

        return quantities

    def get_zone_quantity(self, zona_nombre: str) -> int:
        """
        Cantidad de vehículos en una zona específica.
        """
        for zone in self.zones:
            if zone.name == zona_nombre:
                return zone.detection_count

        return -1  #! Retornar -1 si la zona no se encuentra

    def get_zone_wait_times(self) -> list[int]:
        """
        Tiempos de detección en todas las zonas.
        """
        wait_times: list[int] = []
        for zone in self.zones:
            if "Zona" in zone.name:
                wait_times.append(zone.wait_time)

        return wait_times

    def get_total_wait_time(self) -> int:
        """
        Tiempos de detección en todas las zonas.
        """

        return sum(zona.wait_time for zona in self.zones)

    def get_all_zones(self) -> list[Zone]:
        """
        Devuelve la lista de todas las zonas.
        """
        return self.zones

    def activate_fines(self, zone_name: str) -> bool:
        """
        Activa/desactiva las multas en las zonas.

        Args:
            zona_nombre (str): Nombre de la zona. Ej: "Zona A"

        Returns:
            bool: Estado de las multas de la zona.
        """

        for zone in self.zones:
            if zone.name == zone_name:
                zone.fines_activated = not zone.fines_activated
                return zone.fines_activated

        return False

    def get_zone_by_name(self, zone_name: str) -> Zone | None:
        """
        Devuelve una zona por su nombre.

        Args:
            zona_nombre (str): Nombre de la zona. Ej: "Zona A"

        Returns:
            Zona | None: La zona encontrada o None si no se encuentra.
        """
        for zona in self.zones:
            if zona.name == zone_name:
                return zona

        return None
