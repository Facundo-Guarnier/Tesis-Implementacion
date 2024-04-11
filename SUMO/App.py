import traci

from SUMO.zonas.ZonaList import ZonaList
from SUMO.zonas.Zona import Zona


class App:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            #! Iniciar la simulación de SUMO
            # traci.start(["sumo-gui", "-c", "SUMO/Mapa/osm.sumocfg"])
            traci.start(["sumo-gui", "-c", "SUMO/MapaDe0/mapa.sumocfg"])
        return cls._instance


    def __init__(self):
        self.zonas = ZonaList()
    
    def getVehiculos(self, zona: Zona) -> int:
        """
        Obtener la cantidad de vehículos en una calle
        """
        zona.cantidad_detecciones = traci.edge.getLastStepVehicleNumber(zona.id)
        return zona.cantidad_detecciones


    def cambiarEstado(self, semaforo: str, estado: str) -> None:
        """
        Cambiar el color del semáforo (ejemplo: ponerlo en verde)
        """
        traci.trafficlight.setRedYellowGreenState(semaforo, estado)


    def getSemaforoEstado(self, semaforo: str) -> str:
        """
        Obtener el estado actual del semáforo
        """
        return traci.trafficlight.getRedYellowGreenState(semaforo)    
    
    
    def iniciar_simulacion(self) -> None:
        try: 
            while traci.simulation.getMinExpectedNumber() > 0:
                print(f"\nPaso simulación: {traci.simulation.getTime()}")
                
                #! Establecer la cantidad detectada en cada zona.
                for zona in self.zonas.zonas:
                    print(f"Zona {zona.nombre}: {self.getVehiculos(zona)}")
                
                print(f"Semaforo 1: {self.getSemaforoEstado('1')}")
                print(f"Semaforo 2: {self.getSemaforoEstado('2')}")
                print(f"Semaforo 3: {self.getSemaforoEstado('3')}")
                print(f"Semaforo 4: {self.getSemaforoEstado('4')}")
                
                #! Avanzar la simulación un paso
                traci.simulationStep()
        
            #! Detener la simulación de SUMO al finalizar
            traci.close()
        
        except traci.exceptions.FatalTraCIError as e:
            print(f"Error en la simulación de SUMO: '{e}'")