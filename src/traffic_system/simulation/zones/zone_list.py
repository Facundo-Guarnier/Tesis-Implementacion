from src.traffic_system.simulation.zones.zone import Zone


class ZoneList:
    """
    Clase de tipo "Singleton" que:
    - Representa una lista de zonas (List[Zone]).
    """

    _instance = None  # type: ignore

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.zones = self._define_zones()

    def _define_zones(self) -> list[Zone]:
        """
        Definir las zonas de la simulación.
        """
        # TODO: Eliminar las zonas hardcodeadas y permitir que se definan dinámicamente (config.yaml u otro).
        return [
            Zone(name="Zona A", id="A"),
            Zone(name="Zona B", id="B"),
            Zone(name="Zona C", id="C"),
            Zone(name="Zona D", id="D"),
            Zone(name="Zona E", id="E"),
            Zone(name="Zona F", id="F"),
            Zone(name="Zona G", id="G"),
            Zone(name="Zona H", id="H"),
            Zone(name="Zona I", id="I"),
            Zone(name="Zona J", id="J"),
            Zone(name="Zona K", id="K"),
            Zone(name="Zona L", id="L"),
        ]

    def get_all_zones(self) -> list[Zone]:
        """
        Devuelve la lista de todas las zonas.
        """
        return self.zones
