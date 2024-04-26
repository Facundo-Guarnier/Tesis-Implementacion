import os, traci, logging, inspect
from threading import Thread
from typing import Any

from SUMO.zonas.ZonaList import ZonaList


class AppSUMO:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    
    def __init__(self, gui:bool=False):
        logging.basicConfig(level=logging.DEBUG)
        
        self.zonas = ZonaList()
        self.gui = gui
        self.traci_s1:traci.connection.Connection
        self.traci_s2:traci.connection.Connection
    
    
    def iniciar(self) -> None:
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        logger.info(" Iniciando...")
        if self.gui:
            traci.start(cmd=["sumo-gui", "-c", "SUMO/MapaDe0/mapa.sumocfg"], label="s1")
            self.traci_s1 = traci.getConnection("s1")
            traci.start(cmd=["sumo-gui", "-c", "SUMO/MapaDe0/mapa.sumocfg"], label="s2")
            self.traci_s2 = traci.getConnection("s2") 
        else:
            traci.start(cmd=["sumo", "-c", "SUMO/MapaDe0/mapa.sumocfg"], label="s1")
            self.traci_s1 = traci.getConnection("s1")
            # traci.start(cmd=["sumo", "-c", "SUMO/MapaDe0/mapa.sumocfg"], label="s2")
            # self.traci_s2 = traci.getConnection("s2") 
    
        try: 
            #! Crear una tarea en paralelo con concurrencia para la simulación s2
            Thread(target=self.s2).start()
            
            #! Para que haya un mínimo de vehículos en la simulación.
            while self.traci_s1.simulation.getMinExpectedNumber() > 0 and self.traci_s1.simulation.getTime() < 250:
                self.traci_s1.simulationStep()
                
        except traci.exceptions.FatalTraCIError as e:
            logger.error(f" Error en la simulación de SUMO: '{e}'")
            os._exit(0)
    
    
    def s2(self) -> None:
        """
        Simulación 2 de SUMO para poder comparar valores.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        try:
            while self.traci_s2.simulation.getMinExpectedNumber() > 0 and self.traci_s2.simulation.getTime() < 19500:
                self.traci_s2.simulationStep()
        except traci.exceptions.FatalTraCIError as e:
            logger.error(f" Error en la simulación 2 de SUMO: '{e}'")
            os._exit(0)
        
        except Exception as e:
            logger.error(f" Error en la simulación 2 de SUMO: '{e}'")
            os._exit(0)
    
    
    def setVehiculo(self) -> None:
        """
        Obtener la cantidad de vehículos en una calle
        """
        for zona in self.zonas.zonas:
            zona.cantidad_detecciones = self.traci_s1.edge.getLastStepVehicleNumber(zona.id)
    
    
    def setSemaforoEstado(self, semaforo: str, estado: str) -> None:
        """
        Cambiar el color del semáforo (ejemplo: ponerlo en verde)
        """
        self.traci_s1.trafficlight.setRedYellowGreenState(semaforo, estado)
    
    
    def getSemaforoEstado(self, semaforo: str) -> str:
        """
        Obtener el estado actual del semáforo
        """
        return self.traci_s1.trafficlight.getRedYellowGreenState(semaforo)    
    
    
    def getSemaforosEstados(self) -> list:
        """
        Obtener el estado actual de todos los semáforos.
        """
        return [self.traci_s1.trafficlight.getRedYellowGreenState(semaforo) for semaforo in ["1", "2", "3", "4"]]
    
    
    def getTiempoEspera(self, zona_id:str) -> tuple|Any:
        """
        Obtener el tiempo de espera en una zona.
        """
        #edge.getLastStepVehicleIDs (self, edgeID) -> list(str). Devuelve los identificadores de los vehículos durante el último paso en el borde dado.
        #vehicle.getWaitingTime (self, ID de borde) -> double. Devuelve la suma del tiempo de espera de todos los vehículos actualmente en ese borde (consulte traci.vehicle.getWaitingTime).
        #vehicle.getLastStepHaltingNumber (self, ID de borde) -> int. Devuelve el número total de vehículos detenidos durante el último paso de tiempo en el borde dado. Se considera parada una velocidad inferior a 0,1 m/s.
        
        # t =  traci.vehicle.getWaitingTime()
        # t = traci.edge.getLastStepVehicleIDs()
        
        return  self.traci_s1.edge.getWaitingTime(zona_id)
    
    
    def getTiemposEspera(self, s2=False) -> list:
        """
        Obtener todos los tiempos de espera por en todas las zonas.
        """
        if s2:
            while self.traci_s2.simulation.getTime() < 250:
                self.traci_s2.simulationStep()
            
            return [self.traci_s2.edge.getWaitingTime(zona.id) for zona in self.zonas.zonas]
        
        else:
            while self.traci_s1.simulation.getTime() < 250:
                self.traci_s1.simulationStep()
            
            return [self.traci_s1.edge.getWaitingTime(zona.id) for zona in self.zonas.zonas]
    
    
    def getTiemposEsperaTotal(self, s2=False) -> tuple|Any:
        """
        Obtener el tiempo total de espera en todas las zonas.
        """
        
        if s2:
            while self.traci_s2.simulation.getTime() < 250:
                self.traci_s2.simulationStep()
            return (sum(self.traci_s2.edge.getWaitingTime(zona.id) for zona in self.zonas.zonas))
            
        else:
            while self.traci_s1.simulation.getTime() < 250:
                self.traci_s1.simulationStep()
            return (sum(self.traci_s1.edge.getWaitingTime(zona.id) for zona in self.zonas.zonas))
    
    
    def avanzar(self, steps:int) -> bool:
        """
        Avanzar la cantidad de steps especificada.
        """
        for _ in range(steps):
            if self.puedoSeguir():
                self.traci_s1.simulationStep()
                done = False
            else:
                done = True
                self.reiniciar()
                break
        return done
    
    
    def reiniciar(self) -> None:
        """
        Reiniciar la simulación.
        """
        self.traci_s1.close()
        self.iniciar()
    
    
    def puedoSeguir(self) -> bool:
        """
        Verificar si la simulación puede seguir. Para eso hay que saber:
        - Si está por debajo del tiempo/steps 19500.
        - Si hay vehículos en la simulación.
        """
        return self.traci_s1.simulation.getTime() <= 19500 and self.traci_s1.simulation.getMinExpectedNumber() > 0
    
    
    def getSimulacionOK(self) -> bool:
        """
        Verificar si la simulación está OK.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore

        try:
            estado = self.traci_s1.simulation.getMinExpectedNumber() > 0 and self.traci_s1.simulation.getTime() >= 0
            return estado
        
        except Exception as e:
            logger.error(f" Error en la simulación de SUMO: '{e}'")
            return False