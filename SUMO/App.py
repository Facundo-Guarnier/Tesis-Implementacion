import os, traci, logging, inspect
from threading import Thread
from typing import Any

from SUMO.zonas.ZonaList import ZonaList
from config import configuracion


class AppSUMO:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        
        self.zonas = ZonaList()
        self.traci_s2:traci.connection.Connection|Any = None
        self.__gui = configuracion["sumo"]["gui"]
        self.__comparar = configuracion["sumo"]["comparar"]
    
    
    def iniciar(self) -> None:
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}') # type: ignore
        
        logger.info(" Iniciando...")
        if self.__gui:
            os.environ["SUMO_LOG"] = "error"
            traci.start(cmd=["sumo-gui", "-c", "SUMO/MapaDe0/mapa.sumocfg", "--no-warnings"], label="s1")
            self.traci_s1 = traci.getConnection("s1")
            if self.__comparar:
                traci.start(cmd=["sumo-gui", "-c", "SUMO/MapaDe0/mapa.sumocfg", "--no-warnings"], label="s2")
                self.traci_s2 = traci.getConnection("s2") 
        else:
            traci.start(cmd=["sumo", "-c", "SUMO/MapaDe0/mapa.sumocfg", "--no-warnings"], label="s1")
            self.traci_s1 = traci.getConnection("s1")
        
        try: 
            #! Crear una tarea en paralelo con concurrencia para la simulación s2
            if self.__comparar:
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
                
                #! Cada 15 segundos muestra el tiempo total
                if self.traci_s2.simulation.getTime() % 15 == 0:
                    logger.info(f" (s1: {self.getTiemposEsperaTotal(s2=False)} | s2: {self.getTiemposEsperaTotal(s2=True)})")
                
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
    
    
    def setSemaforoEstado(self, semaforo: str, estado_nuevo: str) -> None:
        """
        Cambiar el color del semáforo (ejemplo: ponerlo en verde)
        """
        estado_actual = self.getSemaforoEstado(semaforo)
        if estado_nuevo != estado_actual:
            estado_amarillo = estado_actual.replace('g', 'y')
            estado_amarillo = estado_amarillo.replace('G', 'y')
            
            self.traci_s1.trafficlight.setRedYellowGreenState(semaforo, estado_amarillo)
            self.avanzar(3)
        
            self.traci_s1.trafficlight.setRedYellowGreenState(semaforo, estado_nuevo)
    
    
    def setSemaforosEstados(self, estados_nuevos: list) -> None:
        """
        Cambiar el color de todos los semáforos.
        
        Args:
            estados_nuevos: Lista de estados de los semáforos. [{'id': '1', 'estado': 'GGGGGGrrrrr'}, {'id': '2', 'estado': 'GGGrrrrrGGg'}, {'id': '3', 'estado': 'GGgGGGrrrrr'}, {'id': '4', 'estado': 'GGGrrrrGGg'}]
        """
        
        estados_amarillos:list[dict] = []
        
        #! Calcular estados amarillos
        for estado in estados_nuevos:
            semaforo_id = estado["id"]
            estado_nuevo = estado["estado"]
            
            estado_actual = self.getSemaforoEstado(semaforo_id)
        
            if estado_nuevo != estado_actual:
                estado_amarillo = estado_actual.replace('g', 'y')
                estado_amarillo = estado_amarillo.replace('G', 'y')
                estados_amarillos.append({"id": semaforo_id, "estado": estado_amarillo})
        
        #! Cambiar a amarillo 
        for estado in estados_amarillos:
            semaforo_id = estado["id"]
            estado_amarillo = estado["estado"]
            self.traci_s1.trafficlight.setRedYellowGreenState(semaforo_id, estado_amarillo)
        
        #! Avanzar 3 segundos para que se vea el amarillo
        self.avanzar(3)
        
        #! Cambiar a verde
        for estado in estados_nuevos:
            semaforo_id = estado["id"]
            estado_nuevo = estado["estado"]
            self.traci_s1.trafficlight.setRedYellowGreenState(semaforo_id, estado_nuevo)
    
    
    def getSemaforoEstado(self, semaforo: str) -> str:
        """
        Obtener el estado actual del semáforo
        """
        return self.traci_s1.trafficlight.getRedYellowGreenState(semaforo)    
    
    
    def getSemaforosEstados(self) -> list[str]:
        """
        Obtener el estado actual de todos los semáforos.
        
        Returns:
            list: ['GGGGGGGGGGg', 'GGGGGGGGGGg', 'GGGGGGGGGGg', 'GGGGGGGGGGg']
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
    
    
    def getTiemposEspera(self, s2=False) -> list[float]:
        """
        Obtener todos los tiempos de espera por en todas las zonas.
        
        Returns:
            list[float]: [1.0, 0.0, 8.0, 0.0, 0.0, 12.0, 2.0, 0.0, 5.0, 0.0, 27.0, 0.0]
        """
        
        if s2:
            #! Tiempo de espera en la simulación 2 
            if self.traci_s2:
                while self.traci_s2.simulation.getTime() < 250:
                    self.traci_s2.simulationStep() 
                
                return [self.traci_s2.edge.getWaitingTime(zona.id) for zona in self.zonas.zonas]
            return [0.0]
        
        else:
            #! Tiempo de espera en la simulación 1 (la principal)
            while self.traci_s1.simulation.getTime() < 250:
                self.traci_s1.simulationStep()
            
            return [self.traci_s1.edge.getWaitingTime(zona.id) for zona in self.zonas.zonas]
    
    
    def getTiemposEsperaTotal(self, s2=False) -> tuple[float]|Any:
        """
        Obtener el tiempo total de espera de todas las zonas juntas.
        
        Return: 
            tuple[float]: (55.0)
        """
        
        if s2:
            #! Tiempo de espera en la simulación 2
            if self.traci_s2:
                while self.traci_s2.simulation.getTime() < 250:
                    self.traci_s2.simulationStep()
                return (sum(self.traci_s2.edge.getWaitingTime(zona.id) for zona in self.zonas.zonas))
            return tuple([-1.0])
        
        else:
            #! Tiempo de espera en la simulación 1 (la principal)
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
    
    
    def getStepsReporte(self) -> int:
        """
        Obtener la cantidad de steps que lleva la simulación, para el reporte.
        Esto es cada x segundos (configurado en el archivo de configuración).
        
        Returns:
            int: 480
        """
        
        while self.traci_s1.simulation.getTime() % configuracion["reporte"]["steps"] != 0:
            pass
        
        return int(self.traci_s1.simulation.getTime())