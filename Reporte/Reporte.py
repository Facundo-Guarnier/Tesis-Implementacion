import os, time, sqlite3, logging, inspect

from Reporte.Api import ApiReporte

from config import configuracion


class Reporte:
    def __init__(self) -> None:
        logging.basicConfig(level=logging.DEBUG)
        self.__api = ApiReporte()
        self.__path_reporte = os.path.join(
            configuracion["reporte"]["path_reporte"],
            f"Reporte_{time.strftime('%Y-%m-%d_%H-%M-%S')}",
        )
        self.__db_conn:sqlite3.Connection|None = None   #! Conexión a la base de datos
        self.__cursor:sqlite3.Cursor|None = None    #! Cursor de la base de datos
        self.__crear_logger()
    
    
    def main(self) -> None:
        """
        Método principal para generar el reporte de la simulación.
        - Crea la carpeta para el reporte.
        - Verifica si la simulación está en curso.
        - Genera el reporte de la simulación.
        """
        logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}')  # type: ignore
        
        #! Verificar si la simulación fue exitosa
        while not self.__api.getSimulacionOK():
            time.sleep(1)
        
        self.__conectar_db()
        self.__crear_tabla()
        
        #! Generar reporte
        e = 0
        while True and e < 5:
            datos = self.__obtener_datos()
            
            if datos == {} or not self.__guardar_reporte(datos=datos):
                logger.error(
                    f" Error al generar el reporte. Reintentando... ({e + 1}/{5})"
                )
                e += 1
                time.sleep(configuracion["reporte"]["tiempo_entre_reportes"])
            
            else:
                e = 0
                self.__alertar(datos=datos)
        
        logger.error(" Falló 5 veces seguidas al intentar generar el reporte.")
        self.__cerrar_db()
    
    
    def __crear_logger(self):
        """
        Crea un logger para registrar las alertas en un archivo .log.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        log_dir = os.path.join(self.__path_reporte)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        #! Crear un manejador de archivos para escribir las alertas en un archivo .log
        file_handler = logging.FileHandler(
            os.path.join(self.__path_reporte, "alertas.log")
        )
        file_handler.setLevel(logging.INFO)
        
        #! Crear un formateador para dar formato a los mensajes de registro
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        
        #! Agregar el manejador de archivos al logger
        self.logger.addHandler(file_handler)
    
    
    def __conectar_db(self) -> None:
        """
        Conecta a la base de datos SQLite.
        """
        self.__db_conn = sqlite3.connect(
            os.path.join(self.__path_reporte, "reporte.db")
        )
        self.__cursor = self.__db_conn.cursor()
    
    
    def __cerrar_db(self) -> None:
        """
        Cierra la conexión a la base de datos.
        """
        if self.__db_conn:
            self.__db_conn.close()
    
    
    def __obtener_datos(self) -> dict:
        """
        Obtener los datos de la simulación.
        
        Returns:
            dict: Datos de la simulación.
        """
        
        if not self.__api.getSimulacionOK():
            return {}
        
        #! Obtener los datos de la simulación
        datos = self.__api.getReporte()
        
        #! Calcular el tiempo de espera total
        total = sum(datos["tiempos_espera"])
        datos["tiempo_espera_total"] = total
        
        return datos
    
    
    def __crear_tabla(self) -> None:
        """
        Crea la tabla en la base de datos SQLite si no existe.
        """
        sql = """
            CREATE TABLE IF NOT EXISTS reporte (
                Steps INTEGER PRIMARY KEY,
                Semaforo1 TEXT,
                Semaforo2 TEXT,
                Semaforo3 TEXT,
                Semaforo4 TEXT,
                TiempoTotal INTEGER,
                ZonaA INTEGER,
                ZonaB INTEGER,
                ZonaC INTEGER,
                ZonaD INTEGER,
                ZonaE INTEGER,
                ZonaF INTEGER,
                ZonaG INTEGER,
                ZonaH INTEGER,
                ZonaI INTEGER,
                ZonaJ INTEGER,
                ZonaK INTEGER,
                ZonaL INTEGER
            );
        """
        if not self.__cursor or not self.__db_conn:
            return
        self.__cursor.execute(sql)
        self.__db_conn.commit()
    
    
    def __guardar_reporte(self, datos: dict) -> bool:
        """
        Guarda los datos del reporte en la base de datos SQLite.
        
        Args:
            datos (dict): Datos de la simulación.
        
        Returns:
            bool: True si se guardaron los datos correctamente, False en caso contrario.
        """
        
        try:
            sql = """
                INSERT INTO reporte (
                    Steps, 
                    Semaforo1, 
                    Semaforo2, 
                    Semaforo3, 
                    Semaforo4, 
                    TiempoTotal, 
                    ZonaA, ZonaB, ZonaC, ZonaD, ZonaE, ZonaF, ZonaG, ZonaH, ZonaI, ZonaJ, ZonaK, ZonaL
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            logger = logging.getLogger(f' {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}')  # type: ignore
            if not self.__cursor:
                return False
            else:
                self.__cursor.execute(
                    sql,
                    (
                        datos["steps"],
                        datos["estados_semaforos"][0],
                        datos["estados_semaforos"][1],
                        datos["estados_semaforos"][2],
                        datos["estados_semaforos"][3],
                        datos["tiempo_espera_total"],
                        datos["tiempos_espera"][0],
                        datos["tiempos_espera"][1],
                        datos["tiempos_espera"][2],
                        datos["tiempos_espera"][3],
                        datos["tiempos_espera"][4],
                        datos["tiempos_espera"][5],
                        datos["tiempos_espera"][6],
                        datos["tiempos_espera"][7],
                        datos["tiempos_espera"][8],
                        datos["tiempos_espera"][9],
                        datos["tiempos_espera"][10],
                        datos["tiempos_espera"][11],
                    ),
                )
                if not self.__db_conn:
                    return False
                else:
                    self.__db_conn.commit()
                    return True
        except Exception as e:
            logger.error(f" Error al guardar el reporte en la base de datos: {e}")
            return False
    
    
    def __alertar(self, datos: dict) -> None:
        """
        Revisa si se tiene que generar alguna alerta. Condiciones: 
        - Tiempo de espera total mayor al tiempo de espera máximo permitido.
        - Tiempo de espera de una zona mayor al tiempo de espera máximo permitido.
        
        Args:
            datos (dict): Datos de la simulación.
        """
        
        if (datos["tiempo_espera_total"] > configuracion["reporte"]["tiempo_total_espera_maximo"]):
            self.logger.warning(
                f"Step {datos['steps']}: Tiempo de espera total mayor al permitido ({datos['tiempo_espera_total']})."
            )
        
        if max(datos["tiempos_espera"]) > configuracion["reporte"]["tiempo_zona_espera_maximo"]:
            indice_zona_maxima = datos["tiempos_espera"].index(max(datos["tiempos_espera"]))
            nombre_zona_maxima = chr(ord('A') + indice_zona_maxima)  #! Convertir índice a letra
            self.logger.warning(
                f"Step {datos['steps']}: Tiempo de espera en la zona {nombre_zona_maxima} mayor permitido ({max(datos['tiempos_espera'])})."
            )