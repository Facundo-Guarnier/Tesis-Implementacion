from __future__ import annotations

from src.traffic_system.simulation.zones.zone import Zone


class ZoneList:
    """
    Clase de tipo "Singleton" que:
    - Representa una lista de zonas (List[Zone]).
    """

    _instance: ZoneList | None = None

    def __new__(cls) -> ZoneList:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.zones = self._define_zones()

    def _define_zones(self) -> list[Zone]:
        """
        Definir las zonas de la simulación.
        """
        # TODO: Eliminar las zonas hardcodeadas y permitir que se definan dinámicamente (config.yaml u otro).
        return [
            Zone(name="Zona A", zone_id="A"),
            Zone(name="Zona B", zone_id="B"),
            Zone(name="Zona C", zone_id="C"),
            Zone(name="Zona D", zone_id="D"),
            Zone(name="Zona E", zone_id="E"),
            Zone(name="Zona F", zone_id="F"),
            Zone(name="Zona G", zone_id="G"),
            Zone(name="Zona H", zone_id="H"),
            Zone(name="Zona I", zone_id="I"),
            Zone(name="Zona J", zone_id="J"),
            Zone(name="Zona K", zone_id="K"),
            Zone(name="Zona L", zone_id="L"),
        ]

    def get_all_zones(self) -> list[Zone]:
        """
        Devuelve la lista de todas las zonas.
        """
        return self.zones
