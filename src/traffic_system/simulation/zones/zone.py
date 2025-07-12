class Zone:
    """
    Clase que representa una zona (calle) en SUMO.
    """

    def __init__(self, name: str, id: str) -> None:
        self.name = name
        self.id = id
        self.wait_time: int = 0
