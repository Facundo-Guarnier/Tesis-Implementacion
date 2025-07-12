class Zone:
    """
    Clase que representa una zona (calle) en SUMO.
    """

    def __init__(self, name: str, zone_id: str) -> None:
        self.name = name
        self.id = zone_id
        self.wait_time: int = 0
