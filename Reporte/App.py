# [CU1]
# Esta seccion le pide información a la API de deteccion y de simulacion para 
# obtener los datos de flujo vehicular y mostrarselos al agente de transito, ya 
# sea en un csv o de otra manera.  
# 
# [CU2]
# En base a la información obtenida se pueden realizar las alertas correspondientes 
# para el segundo caso de usuario.

import inspect, logging
from Reporte.Reporte import Reporte



class AppReporte:
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.reporte = Reporte()
    
    def generar_reporte(self) -> None:
        """
        Generar reporte.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}')  # type: ignore
        logger.info("Generar reporte")
        
        self.reporte.main()