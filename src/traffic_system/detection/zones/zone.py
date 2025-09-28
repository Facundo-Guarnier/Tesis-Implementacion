import numpy as np

from src.traffic_system.core.types import Resolution


class Zone:
    """
    Clase que representa una zona de la pantalla.
    - Puntos: np.array de puntos_originales (x, y) que representan los vértices de la zona.
    - Resolución: resolución de la pantalla en la que se ha tomado la zona.
    - Puntos reescalados: puntos_originales reescalados a la resolución de la pantalla en la que se va a mostrar la zona.
    - Cantidad de detecciones: cantidad de detecciones que han ocurrido en la zona.

    Attributes:
        - nombre (str): Nombre de la zona. Ejemplo: "Zona A".
        - resolucion (tuple): Resolución de la pantalla en la que se ha tomado la zona.
        - puntos_originales (np.ndarray): Puntos de la zona en la resolución original.
        - puntos_reescalados (np.ndarray): Puntos de la zona reescalados a la resolución objetivo.

        - multas_activadas (bool): Indica si las multas están activadas en la zona.

        - cantidad_detecciones (int): Cantidad de detecciones que han ocurrido en la zona.
        - tiempo_espera (int): Tiempo de espera en la zona.
    """

    def __init__(
        self,
        name: str,
        resolution: Resolution,
        original_points: np.ndarray,
        original_fine_points: np.ndarray,
    ) -> None:
        self.name = name
        self._resolution = resolution
        self.original_points = original_points
        self.rescaled_points = original_points

        self.fines_activated: bool = False
        self.original_fine_points: np.ndarray = original_fine_points
        self.rescaled_fine_points: np.ndarray = original_fine_points

        self.detection_count: int = 0
        self.wait_time: int = 0

    def scale_points(self, target_resolution: Resolution) -> None:
        """
        Escala los puntos_originales de la zona a la resolución objetivo.
        """
        if self._resolution != target_resolution:
            target_points = []

            for i, point in enumerate(self.original_points):
                try:
                    original_x, original_y = point

                    # Validar que los valores sean numéricos (incluye tipos numpy)
                    if not isinstance(
                        original_x, int | float | np.integer | np.floating
                    ) or not isinstance(
                        original_y, int | float | np.integer | np.floating
                    ):
                        raise TypeError(
                            f"Coordenadas del punto {i} no son numéricas: x={original_x} (type: {type(original_x)}), y={original_y} (type: {type(original_y)})"
                        )

                    original_width, original_height = self._resolution
                    target_width, target_height = target_resolution

                    #! Calcular las proporciones de escala en x e y
                    scale_x = target_width / original_width
                    scale_y = target_height / original_height

                    #! Aplicar la escala al punto
                    target_x = int(original_x * scale_x)
                    target_y = int(original_y * scale_y)

                    target_points.append([target_x, target_y])
                except (ValueError, TypeError) as e:
                    raise TypeError(
                        f"Error al escalar punto {i} en zona '{self.name}': {e}. Verifique que las coordenadas en zones.yaml sean números válidos."
                    ) from e

            self.rescaled_points = np.array(target_points)

    def scale_fine_points(self, target_resolution: Resolution) -> None:
        """
        Escala los puntos originales de la multas de la zona a la resolución objetivo.

        Args:
            resolucion_objetivo (tuple): Resolución a la que se quiere escalar los puntos de la multa.
        """

        if self._resolution != target_resolution:
            target_points = []

            for i, point in enumerate(self.original_fine_points):
                try:
                    original_x, original_y = point

                    # Validar que los valores sean numéricos (incluye tipos numpy)
                    if not isinstance(
                        original_x, int | float | np.integer | np.floating
                    ) or not isinstance(
                        original_y, int | float | np.integer | np.floating
                    ):
                        raise TypeError(
                            f"Coordenadas del punto de multa {i} no son numéricas: x={original_x} (type: {type(original_x)}), y={original_y} (type: {type(original_y)})"
                        )

                    original_width, original_height = self._resolution
                    target_width, target_height = target_resolution

                    #! Calcular las proporciones de escala en x e y
                    scale_x = target_width / original_width
                    scale_y = target_height / original_height

                    #! Aplicar la escala al punto
                    target_x = int(original_x * scale_x)
                    target_y = int(original_y * scale_y)

                    target_points.append([target_x, target_y])
                except (ValueError, TypeError) as e:
                    raise TypeError(
                        f"Error al escalar punto de multa {i} en zona '{self.name}': {e}. Verifique que las coordenadas en zones.yaml sean números válidos."
                    ) from e

            self.rescaled_fine_points = np.array(target_points)

    def __str__(self) -> str:
        return f"{self.name} ({self._resolution[0]}x{self._resolution[1]})"
