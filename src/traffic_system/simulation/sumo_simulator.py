import logging
from typing import Any

import traci

from ..core.config_models import SumoSettings


class SumoSimulator:
    def __init__(self, sumo_settings: SumoSettings):
        # 1. INYECCIÓN DE DEPENDENCIAS: La configuración se recibe, no se importa globalmente.
        self.settings = sumo_settings
        self.logger = logging.getLogger(self.__class__.__name__)

        self.traci_s1: traci.connection.Connection | Any = None
        # La lógica de comparación (s2) la sacaremos, porque no es responsabilidad
        # de un simulador compararse a sí mismo. Eso es tarea de un script de análisis.

        # El resto de atributos se mantienen si son necesarios para el estado interno.
        # ...

    def start(self) -> None:
        """Inicia la conexión con la simulación principal de SUMO."""
        self.logger.info("Iniciando conexión con SUMO...")

        # 2. USA LA CONFIGURACIÓN INYECTADA:
        # Ya no usamos 'app_settings["sumo"]["gui"]', sino 'self.settings.gui'
        cmd = ["sumo-gui" if self.settings.gui else "sumo"]
        cmd.extend(
            ["-c", "assets/sumo_maps/MapaDe0/mapa.sumocfg", "--no-warnings"]
        )  # Rutas relativas o desde config

        # La gestión de los hilos y múltiples conexiones (s1, s2) se moverá
        # a un script de análisis o a la clase Application, no vive aquí.

        # Aquí solo iniciamos UNA conexión.
        try:
            traci.start(cmd, label="s1")
            self.traci_s1 = traci.getConnection("s1")
            self.logger.info("Conexión con SUMO establecida.")
        except Exception as e:
            self.logger.error(f"No se pudo iniciar SUMO: {e}")
            raise  # Lanzamos la excepción para que el llamador decida qué hacer.

    # --- El resto de métodos refactorizados ---
    # Todos los métodos ahora usan 'self.traci_s1' y 'self.settings'

    def set_traffic_light_state(self, light_id: str, new_state: str) -> None:
        """Cambia el estado de un semáforo, incluyendo la transición a amarillo."""
        # ... (la lógica que ya tenías, pero más limpia) ...

    def get_traffic_state(self) -> dict:
        """
        Devuelve el estado actual del tráfico en un formato consistente.
        Este método es el que implementaría la interfaz DataProvider que discutimos.
        """
        # ... Lógica para obtener número de vehículos, tiempo de espera, etc. ...
        # Devuelve un diccionario estandarizado.
        return {"zonas": [...], "tiempo_espera_total": ...}

    def close(self) -> None:
        """Cierra la conexión con TraCI."""
        if self.traci_s1:
            self.traci_s1.close()
            self.logger.info("Conexión con SUMO cerrada.")

    # El resto de métodos como getTiempoEspera, getCantidadVehiculos, etc. se
    # simplifican para operar solo sobre 'self.traci_s1'.
