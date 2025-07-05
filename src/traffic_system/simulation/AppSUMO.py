import logging
from typing import Any

import traci

from src.traffic_system.simulation.zonas.ZonaList import ZonaList


class AppSUMO:
    def __init__(
        self,
        traci_conn: traci.connection.Connection | Any,
        zonas: ZonaList,
        label: str,
    ) -> None:
        """
        Una clase de servicio que encapsula las interacciones con una única
        instancia de simulación de SUMO a través de Traci.

        Args:
            traci_conn: El objeto de conexión Traci ya iniciado.
            zonas: Una instancia de ZonaList con la definición de las zonas.
            label: Una etiqueta para identificar esta instancia de simulación (ej. 's1').
        """
        self.traci = traci_conn
        self.zonas = zonas
        self.label = label
        self.logger = logging.getLogger(f" {self.__class__.__name__}[{self.label}]")

    def setSemaforoEstado(self, semaforo: str, estado_nuevo: str) -> None:
        """
        Cambiar el color del semáforo (ejemplo: ponerlo en verde).
        """
        estado_actual = self.getSemaforoEstado(semaforo)
        if estado_nuevo != estado_actual:
            estado_amarillo = estado_actual.replace("g", "y").replace("G", "y")

            self.traci.trafficlight.setRedYellowGreenState(semaforo, estado_amarillo)
            self.avanzar(3)  # Avanza 3 segundos para el amarillo

            self.traci.trafficlight.setRedYellowGreenState(semaforo, estado_nuevo)

    def setSemaforosEstados(self, estados_nuevos: list[dict]) -> None:
        """
        Cambiar el color de varios semáforos de forma coordinada.

        Args:
            estados_nuevos: [{'id': '1', 'estado': 'GGGrrr...'}, ...]
        """
        estados_amarillos: list[dict] = []

        # Calcular estados amarillos solo para los que cambian
        for semaforo_data in estados_nuevos:
            semaforo_id = semaforo_data["id"]
            estado_nuevo = semaforo_data["estado"]
            estado_actual = self.getSemaforoEstado(semaforo_id)

            if estado_nuevo != estado_actual:
                estado_amarillo = estado_actual.replace("g", "y").replace("G", "y")
                estados_amarillos.append({"id": semaforo_id, "estado": estado_amarillo})

        # Poner todos los semáforos que cambian en amarillo
        for semaforo_data in estados_amarillos:
            self.traci.trafficlight.setRedYellowGreenState(
                semaforo_data["id"], semaforo_data["estado"]
            )

        # Si hubo cambios, avanzar para que el amarillo sea visible
        if estados_amarillos:
            self.avanzar(3)

        # Poner todos los semáforos en su estado verde/rojo final
        for semaforo_data in estados_nuevos:
            self.traci.trafficlight.setRedYellowGreenState(
                semaforo_data["id"], semaforo_data["estado"]
            )

    def getSemaforoEstado(self, semaforo: str) -> str:
        """Obtener el estado actual de un semáforo."""
        return self.traci.trafficlight.getRedYellowGreenState(semaforo)

    def getSemaforosEstados(self) -> list[str]:
        """Obtener el estado actual de todos los semáforos principales."""
        return [self.getSemaforoEstado(semaforo) for semaforo in ["1", "2", "3", "4"]]

    def getTiempoEspera(self, zona_id: str) -> float:
        """Obtener el tiempo de espera en una zona."""
        return self.traci.edge.getWaitingTime(zona_id)

    def getTiemposEspera(self) -> list[float]:
        """Obtener todos los tiempos de espera por en todas las zonas."""
        return [self.traci.edge.getWaitingTime(zona.id) for zona in self.zonas.zonas]

    def getTiemposEsperaTotal(self) -> float:
        """Obtener el tiempo total de espera de todas las zonas juntas."""
        return sum(self.getTiemposEspera())

    def getCantidadVehiculos(self) -> int:
        """Obtener la cantidad de vehículos en la simulación."""
        return self.traci.simulation.getMinExpectedNumber()

    def avanzar(self, steps: int) -> bool:
        """
        Avanzar la cantidad de steps especificada.
        Devuelve True si la simulación terminó durante el avance.
        """
        tiempo_inicial = self.traci.simulation.getTime()
        self.logger.debug(f"Avanzando {steps} pasos desde t={tiempo_inicial:.1f}s...")

        done = False
        pasos_ejecutados = 0

        for i in range(steps):
            if self.puedo_seguir():
                try:
                    self.traci.simulationStep()
                    pasos_ejecutados += 1
                except Exception as e:
                    self.logger.error(f"Error ejecutando paso {i+1}: {e}")
                    done = True
                    break
            else:
                # TODO: este log solo sale cuando termina la simulacion con los 19500 pasos. Eliminar?
                done = True
                self.logger.info(
                    f"Simulación {self.label} terminó en paso {i+1} de {steps}"
                )
                break

        tiempo_final = self.traci.simulation.getTime()
        self.logger.debug(
            f"Simulación {self.label}: {pasos_ejecutados}/{steps} pasos ejecutados, "
            f"t={tiempo_inicial:.1f}s -> {tiempo_final:.1f}s, done={done}"
        )

        return done

    def puedo_seguir(self) -> bool:
        """
        Verificar si la simulación puede continuar.
        - Si está por debajo del tiempo/steps 19500.
        - Si hay vehículos en la simulación.
        """
        # El límite de tiempo es una regla de negocio, podría externalizarse
        return (
            self.traci.simulation.getTime() <= 19500
            and self.traci.simulation.getMinExpectedNumber() > 0
        )

    def getSimulacionOK(self) -> bool:
        """
        Verificar si la conexión con la simulación está activa.
        """
        try:
            self.traci.simulation.getTime()
            return True
        except (traci.TraCIException, AttributeError):
            self.logger.error("La conexión con la simulación no está disponible.")
            return False
