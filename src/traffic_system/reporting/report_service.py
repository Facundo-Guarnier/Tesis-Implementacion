import inspect
import logging
import os
import sqlite3
import time
from typing import Any, cast

from src.traffic_system.api_client.reporting_client import ReportAPI
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import ReporteSettings


class ReportService:
    def __init__(self, reporte_settings: ReporteSettings | None = None) -> None:
        # TODO: Eliminar el uso de load_app_settings, ya que deberia cargar desde la configuración global.
        self.settings = load_app_settings().reporte

        logging.basicConfig(level=logging.DEBUG)
        self._client_api_report = ReportAPI()
        self._report_path = os.path.join(
            self.settings.path_reporte,
            f"report_{time.strftime('%Y-%m-%d_%H-%M-%S')}",
        )
        self._db_connection: sqlite3.Connection | None = (
            None  #! Conexión a la base de datos
        )
        self._cursor: sqlite3.Cursor | None = None  #! Cursor de la base de datos
        self._create_logger()

    def generate_report(self) -> None:
        """
        Método principal para generar el reporte de la simulación.
        - Crea la carpeta para el reporte.
        - Verifica si la simulación está en curso.
        - Genera el reporte de la simulación.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        #! Verificar si la simulación fue exitosa
        while not self._client_api_report.is_simulation_running():
            time.sleep(1)

        self._connect_db()
        self._create_table()

        #! Generar reporte
        retries = 0
        while True and retries < 5:
            data = self._get_data()

            if data == {} or not self._save_report(data=data):
                logger.error(
                    f"❌ Error al generar el reporte. Reintentando... ({retries + 1}/{5})"
                )
                retries += 1
                time.sleep(self.settings.tiempo_entre_reportes)

            else:
                retries = 0
                self._check_and_alert(data=data)

        logger.error("❌ Falló 5 veces seguidas al intentar generar el reporte.")
        self._close_db()

    def _create_logger(self) -> None:
        """
        Crea un logger para registrar las alertas en un archivo .log.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        log_dir = os.path.join(self._report_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        #! Crear un manejador de archivos para escribir las alertas en un archivo .log
        file_handler = logging.FileHandler(
            os.path.join(self._report_path, "alertas.log")
        )
        file_handler.setLevel(logging.INFO)

        #! Crear un formateador para dar formato a los mensajes de registro
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        #! Agregar el manejador de archivos al logger
        self.logger.addHandler(file_handler)

    def _connect_db(self) -> None:
        """
        Conecta a la base de datos SQLite.
        """
        self._db_connection = sqlite3.connect(
            os.path.join(self._report_path, "reporte.db")
        )
        self._cursor = self._db_connection.cursor()

    def _close_db(self) -> None:
        """
        Cierra la conexión a la base de datos.
        """
        if self._db_connection:
            self._db_connection.close()

    def _get_data(self) -> dict:
        """
        Obtener los datos de la simulación.

        Returns:
            dict: Datos de la simulación. Ej: {
                "steps": 600,
                "tiempo_espera_total": 750,
                "tiempos_espera": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200]
            }
        """

        if not self._client_api_report.is_simulation_running():
            return {}  #! Obtener los datos de la simulación
        data_response = self._client_api_report.get_report()

        if data_response is None:
            return {}

        # Convertir la respuesta Pydantic a diccionario
        data = data_response.model_dump()

        #! Calcular el tiempo de espera total
        # ? Esto es redundante si get_report ya devuelve "total_wait_time"?
        total_wait = float(
            sum(data["wait_times_per_zone"])
        )  # Asumiendo que esta es la clave de la API
        data["tiempo_espera_total"] = total_wait

        # TODO: Implementar mejor tipado
        return cast(dict[Any, Any], data)

    def _create_table(self) -> None:
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
        if not self._cursor or not self._db_connection:
            return
        self._cursor.execute(sql)
        self._db_connection.commit()

    def _save_report(self, data: dict) -> bool:
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
            logger = logging.getLogger(
                f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
            )
            if not self._cursor:
                return False
            else:
                self._cursor.execute(
                    sql,
                    (
                        data["steps"],
                        data["estados_semaforos"][0],
                        data["estados_semaforos"][1],
                        data["estados_semaforos"][2],
                        data["estados_semaforos"][3],
                        data["tiempo_espera_total"],
                        data["tiempos_espera"][0],
                        data["tiempos_espera"][1],
                        data["tiempos_espera"][2],
                        data["tiempos_espera"][3],
                        data["tiempos_espera"][4],
                        data["tiempos_espera"][5],
                        data["tiempos_espera"][6],
                        data["tiempos_espera"][7],
                        data["tiempos_espera"][8],
                        data["tiempos_espera"][9],
                        data["tiempos_espera"][10],
                        data["tiempos_espera"][11],
                    ),
                )
                if not self._db_connection:
                    return False
                else:
                    self._db_connection.commit()
                    return True
        except Exception as e:
            logger.error(f"❌ Error al guardar el reporte en la base de datos: {e}")
            return False

    def _check_and_alert(self, data: dict) -> None:
        """
        Revisa si se tiene que generar alguna alerta. Condiciones:
        - Tiempo de espera total mayor al tiempo de espera máximo permitido.
        - Tiempo de espera de una zona mayor al tiempo de espera máximo permitido.

        Args:
            datos (dict): Datos de la simulación.
        """

        if data["tiempo_espera_total"] > self.settings.tiempo_total_espera_maximo:
            self.logger.warning(
                f"⚠️ Step {data['steps']}: Tiempo de espera total mayor al permitido ({data['tiempo_espera_total']})."
            )

        for i, zone_wait_time in enumerate(data["tiempos_espera"]):
            if zone_wait_time > self.settings.tiempo_zona_espera_maximo:
                max_wait_zone_name = chr(ord("A") + i)  #! Convertir índice a letra
                self.logger.warning(
                    f"⚠️ Step {data['steps']}: Tiempo de espera en la zona {max_wait_zone_name} mayor permitido ({zone_wait_time})."
                )
