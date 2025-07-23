import logging
from collections.abc import Callable

import traci

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import SumoSettings
from src.traffic_system.simulation.zones.zone_list import ZoneList


class SumoApp:
    def __init__(
        self,
        traci_conn: traci.connection.Connection,
        zones: ZoneList,
        label: str,
        config_file: str,
        use_gui: bool,
        restart_callback: (
            Callable[[str, str, bool], traci.connection.Connection] | None
        ) = None,
        sumo_settings: SumoSettings | None = None,
    ) -> None:
        """
        Una clase de servicio que encapsula las interacciones con una única
        instancia de simulación de SUMO a través de Traci.

        Args:
            traci_conn: El objeto de conexión Traci ya iniciado.
            zonas: Una instancia de ZoneList con la definición de las zonas.
            label: Una etiqueta para identificar esta instancia de simulación (ej. 's1').
            config_file: Ruta al archivo de configuración de SUMO.
            use_gui: Si usar la interfaz gráfica de SUMO.
            restart_callback: Función que puede recrear la conexión traci cuando se necesite reiniciar.
        """
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings().sumo

        self.traci = traci_conn
        self.zones = zones
        self.label = label
        self.config_file = config_file
        self.use_gui = use_gui
        self.restart_callback = restart_callback
        self.logger = logging.getLogger(f" {self.__class__.__name__}[{self.label}]")

    def set_traffic_light_state(self, traffic_light_id: str, new_state: str) -> bool:
        """
        Cambiar el color del semáforo (ejemplo: ponerlo en verde).

        Returns:
            bool: True si la simulación terminó durante el cambio, False en caso contrario
        """
        initial_time = self.traci.simulation.getTime()
        self.logger.debug(
            f"🚦 set_traffic_light_state({traffic_light_id}, {new_state}) desde t={initial_time:.1f}s"
        )

        current_state = self.get_traffic_light_state(traffic_light_id)
        if new_state != current_state:
            yellow_state = current_state.replace("g", "y").replace("G", "y")

            self.traci.trafficlight.setRedYellowGreenState(
                traffic_light_id, yellow_state
            )
            # Avanzar para mostrar el amarillo - verificar si termina la simulación
            self.logger.debug("🟡 Mostrando amarillo durante 3 pasos...")
            done = self.advance(3)
            if done:
                self.logger.info(
                    f"🏁 Simulación terminó durante cambio de semáforo {traffic_light_id} (amarillo)"
                )
                return True

            self.traci.trafficlight.setRedYellowGreenState(traffic_light_id, new_state)
            self.logger.debug(f"✅ Semáforo {traffic_light_id} cambiado a {new_state}")
        else:
            self.logger.debug(
                f"⏭️ Semáforo {traffic_light_id} ya está en {new_state}, no necesita cambio"
            )

        return False

    def set_traffic_light_states(self, new_states: list[dict]) -> bool:
        """
        Cambiar el color de varios semáforos de forma coordinada.

        Args:
            estados_nuevos: [{'id': '1', 'estado': 'GGGrrr...'}, ...]

        Returns:
            bool: True si la simulación terminó durante el cambio, False en caso contrario
        """
        yellow_states_list: list[dict] = []

        # Calcular estados amarillos solo para los que cambian
        for traffic_light_data in new_states:
            traffic_light_id = traffic_light_data["id"]
            new_state = traffic_light_data["estado"]
            current_state = self.get_traffic_light_state(traffic_light_id)

            if new_state != current_state:
                yellow_state = current_state.replace("g", "y").replace("G", "y")
                yellow_states_list.append(
                    {"id": traffic_light_id, "estado": yellow_state}
                )

        # Poner todos los semáforos que cambian en amarillo
        for traffic_light_data in yellow_states_list:
            self.traci.trafficlight.setRedYellowGreenState(
                traffic_light_data["id"], traffic_light_data["estado"]
            )

        # Si hubo cambios, avanzar para que el amarillo sea visible
        if yellow_states_list:
            done = self.advance(3)
            if done:
                return True

        # Poner todos los semáforos en su estado verde/rojo final
        for traffic_light_data in new_states:
            self.traci.trafficlight.setRedYellowGreenState(
                traffic_light_data["id"], traffic_light_data["estado"]
            )

        return False

    def get_traffic_light_state(self, traffic_light_id: str) -> str:
        """Obtener el estado actual de un semáforo."""
        # TODO: Mejorar el tipado para "traci" ya que no podemos ver el tipado de getRedYellowGreenState
        return str(self.traci.trafficlight.getRedYellowGreenState(traffic_light_id))

    def get_traffic_light_states(self) -> list[str]:
        """Obtener el estado actual de todos los semáforos principales."""
        return [
            self.get_traffic_light_state(traffic_light_id)
            for traffic_light_id in ["1", "2", "3", "4"]
        ]

    def get_zone_wait_time(self, zone_id: str) -> float:
        """Obtener el tiempo de espera en una zona."""
        # TODO: Mejorar el tipado para "traci" ya que no podemos ver el tipado
        return float(self.traci.edge.getWaitingTime(zone_id))

    def get_wait_times(self) -> list[float]:
        """Obtener todos los tiempos de espera por en todas las zonas."""
        # return [self.traci.edge.getWaitingTime(zone.id) for zone in self.zones.zones]
        return [self.get_zone_wait_time(zone.id) for zone in self.zones.zones]

    def get_total_wait_time(self) -> float:
        """Obtener el tiempo total de espera de todas las zonas juntas."""
        return sum(self.get_wait_times())

    def get_vehicle_count(self) -> int:
        """Obtener la cantidad de vehículos en la simulación."""
        # TODO: Mejorar el tipado para "traci" ya que no podemos ver el tipado
        return int(self.traci.simulation.getMinExpectedNumber())

    def advance(self, steps: int) -> bool:
        """
        Avanzar la cantidad de steps especificada.
        Devuelve True si la simulación terminó durante el avance.
        NOTA: No reinicia automáticamente - el llamador debe llamar reset() si done=True.
        """
        initial_time = self.traci.simulation.getTime()

        #! VERIFICACIÓN CONSERVADORA: Si estamos cerca del límite, verificar si podemos completar TODOS los pasos
        current_time = self.traci.simulation.getTime()
        time_after_all_steps = current_time + steps

        if time_after_all_steps >= self.settings.simulation_time_limit:
            return True

        # Si no vamos a sobrepasar el límite, proceder normalmente
        done = False
        steps_executed = 0

        for i in range(steps):
            # Verificar ANTES de ejecutar el paso
            if not self.can_continue():
                done = True
                self.logger.debug(
                    f"🏁 Simulación {self.label} terminó ANTES del paso {i+1} en t={self.traci.simulation.getTime():.1f}s"
                )
                break

            try:
                # Ejecutar el paso de simulación
                self.traci.simulationStep()
                steps_executed += 1

                # Verificar DESPUÉS de ejecutar el paso - puede que ahora haya terminado
                if not self.can_continue():
                    done = True
                    self.logger.debug(
                        f"🏁 Simulación {self.label} terminó DESPUÉS del paso {i+1} en t={self.traci.simulation.getTime():.1f}s"
                    )
                    break

            except Exception as e:
                self.logger.error(f"Error ejecutando paso {i+1}: {e}")
                # Si hay error durante simulationStep, verificar si es porque terminó
                try:
                    if not self.can_continue():
                        done = True
                        self.logger.debug(
                            f"🏁 Simulación {self.label} terminó por límite después de error en paso {i+1}"
                        )
                    else:
                        done = False
                        self.logger.error(f"❌ Error real en simulationStep: {e}")
                except Exception as e:
                    # Si no podemos verificar can_continue, asumir que terminó por error
                    done = False
                break

        final_time = self.traci.simulation.getTime()

        # Solo hacer debug logging cuando sea relevante
        if initial_time > 19480 or initial_time < 10 or done:
            self.logger.debug(
                f"✅ Simulación {self.label}: {steps_executed}/{steps} pasos ejecutados, "
                f"t={initial_time:.1f}s -> {final_time:.1f}s, done={done}"
            )

        return done

    def reset(self) -> None:
        """
        Reiniciar la simulación.
        """
        self.logger.info("🔄 Reiniciando simulación")

        try:
            # Cerrar la conexión actual
            self.traci.close()
        except Exception as e:
            self.logger.warning(f"Error al cerrar conexión anterior: {e}")

        # Usar el callback para recrear la conexión si está disponible
        if self.restart_callback:
            try:
                self.traci = self.restart_callback(
                    self.label, self.config_file, self.use_gui
                )
                self.logger.info("✅ Simulación reiniciada exitosamente")
            except Exception as e:
                self.logger.error(f"❌ Error al reiniciar la simulación: {e}")
                raise
        else:
            self.logger.error(
                "❌ No se puede reiniciar: no hay callback de reinicio configurado"
            )
            raise RuntimeError(
                "No se puede reiniciar la simulación: callback no disponible"
            )

    def can_continue(self) -> bool:
        """
        Verificar si la simulación puede continuar.
        - Si está por debajo del tiempo/steps 19500.
        - Si hay vehículos en la simulación.
        """
        current_time = self.traci.simulation.getTime()
        vehicle_count = self.get_vehicle_count()
        time_ok = current_time < self.settings.simulation_time_limit
        vehicles_ok = vehicle_count > 0

        can_continue = time_ok and vehicles_ok

        return can_continue

    def is_simulation_active(self) -> bool:
        """
        Verificar si la conexión con la simulación está activa.
        """
        try:
            self.traci.simulation.getTime()
            return True
        except (traci.TraCIException, AttributeError):
            self.logger.error("La conexión con la simulación no está disponible.")
            return False
