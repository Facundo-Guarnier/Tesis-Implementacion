import inspect
import logging
import os
import sqlite3
import time

from pydantic import ValidationError

from src.traffic_system.api_client.reporting_client import ReportAPI
from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.core.config_models import ReportData, ReporteSettings


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
        last_reported_step = -1  # Rastrear el último step reportado

        while True:
            data = self._get_data()
            if data is None:
                logger.error("❌ Error al obtener datos del reporte. Reintentando...")
                time.sleep(5)
                continue

            # Solo procesar si han pasado suficientes steps desde el último reporte
            steps_difference = data.steps - last_reported_step
            print(
                f"Step {data.steps} → Último reportado: {last_reported_step} → Diferencia: {steps_difference}"
            )
            if steps_difference >= self.settings.steps:
                print("++++++++++++++++++++++++++++++++++++++++++++++++++2")
                if self._save_report(data=data):
                    last_reported_step = data.steps
                    print(last_reported_step)
                    self._check_and_alert(data=data)
                    logger.info(f"✅ Reporte guardado para step {data.steps}")
                else:
                    logger.error(
                        f"❌ Error al guardar el reporte para step {data.steps}"
                    )
            else:
                # Esperar un poco antes de verificar nuevamente
                time.sleep(1)  # 1 segundo entre verificaciones

        # logger.error("❌ Falló 5 veces seguidas al intentar generar el reporte.")
        # self._close_db()

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

    def _get_data(self) -> ReportData | None:
        """
        Obtener los datos de la simulación.

        Returns:
            ReportData | None: Datos validados de la simulación o None si hay error.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )

        if not self._client_api_report.is_simulation_running():
            return None

        data_response = self._client_api_report.get_report()
        if data_response is None:
            return None

        try:
            # Convertir la respuesta Pydantic a diccionario
            raw_data = data_response.model_dump()

            # Validar y estructurar los datos usando el modelo ReportData
            validated_data = ReportData(**raw_data)
            logger.info(
                f"✅ Datos del reporte validados correctamente: steps={validated_data.steps}"
            )
            return validated_data

        except ValidationError as e:
            logger.error(f"❌ Error de validación en datos del reporte: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado al procesar datos del reporte: {e}")
            return None

    def _create_table(self) -> None:
        """
        Crea la tabla en la base de datos SQLite si no existe.
        """
        sql = """
            CREATE TABLE IF NOT EXISTS reporte (
                Steps INTEGER PRIMARY KEY,
                Status TEXT,
                Timestamp TEXT,
                Semaforo1 TEXT,
                Semaforo2 TEXT,
                Semaforo3 TEXT,
                Semaforo4 TEXT,
                TiempoTotal REAL,
                ZonaA REAL,
                ZonaB REAL,
                ZonaC REAL,
                ZonaD REAL,
                ZonaE REAL,
                ZonaF REAL,
                ZonaG REAL,
                ZonaH REAL,
                ZonaI REAL,
                ZonaJ REAL,
                ZonaK REAL,
                ZonaL REAL,
                VehiculosZonaA INTEGER,
                VehiculosZonaB INTEGER,
                VehiculosZonaC INTEGER,
                VehiculosZonaD INTEGER,
                VehiculosZonaE INTEGER,
                VehiculosZonaF INTEGER,
                VehiculosZonaG INTEGER,
                VehiculosZonaH INTEGER,
                VehiculosZonaI INTEGER,
                VehiculosZonaJ INTEGER,
                VehiculosZonaK INTEGER,
                VehiculosZonaL INTEGER,
                GeneratedAt TEXT
            );
        """
        if not self._cursor or not self._db_connection:
            return
        self._cursor.execute(sql)
        self._db_connection.commit()

    def _save_report(self, data: ReportData) -> bool:
        """
        Guarda los datos del reporte en la base de datos SQLite.

        Args:
            data (ReportData): Datos validados de la simulación.

        Returns:
            bool: True si se guardaron los datos correctamente, False en caso contrario.
        """

        try:
            print("++++++++++++++++++++++++++++++++++++++++++++++++++1")
            sql = """
                INSERT OR REPLACE INTO reporte (
                    Steps, Status, Timestamp,
                    Semaforo1, Semaforo2, Semaforo3, Semaforo4,
                    TiempoTotal,
                    ZonaA, ZonaB, ZonaC, ZonaD, ZonaE, ZonaF, ZonaG, ZonaH, ZonaI, ZonaJ, ZonaK, ZonaL,
                    VehiculosZonaA, VehiculosZonaB, VehiculosZonaC, VehiculosZonaD, VehiculosZonaE, VehiculosZonaF,
                    VehiculosZonaG, VehiculosZonaH, VehiculosZonaI, VehiculosZonaJ, VehiculosZonaK, VehiculosZonaL,
                    GeneratedAt
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            logger = logging.getLogger(
                f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
            )
            print("++++++++++++++++++++++++++++++++++++++++++++++++++2")
            if not self._cursor:
                print("++++++++++++++++++++++++++++++++++++++++++++++++++3")
                return False
            else:
                print("++++++++++++++++++++++++++++++++++++++++++++++++++4")
                # Usar los métodos del modelo para obtener datos estructurados
                vehiculos_ordenados = data.get_vehiculos_ordenados()
                tiempo_espera_total = data.get_tiempo_espera_total()
                print("++++++++++++++++++++++++++++++++++++++++++++++++++5")
                print(
                    f"Datos validados: steps={data.steps}, status={data.status}, tiempo_total={tiempo_espera_total}"
                )
                print("++++++++++++++++++++++++++++++++++++++++++++++++++5")

                self._cursor.execute(
                    sql,
                    (
                        data.steps,
                        data.status,
                        data.timestamp,
                        data.estados_semaforos[0],
                        data.estados_semaforos[1],
                        data.estados_semaforos[2],
                        data.estados_semaforos[3],
                        tiempo_espera_total,
                        data.tiempos_espera[0],
                        data.tiempos_espera[1],
                        data.tiempos_espera[2],
                        data.tiempos_espera[3],
                        data.tiempos_espera[4],
                        data.tiempos_espera[5],
                        data.tiempos_espera[6],
                        data.tiempos_espera[7],
                        data.tiempos_espera[8],
                        data.tiempos_espera[9],
                        data.tiempos_espera[10],
                        data.tiempos_espera[11],
                        vehiculos_ordenados[0],  # VehiculosZonaA
                        vehiculos_ordenados[1],  # VehiculosZonaB
                        vehiculos_ordenados[2],  # VehiculosZonaC
                        vehiculos_ordenados[3],  # VehiculosZonaD
                        vehiculos_ordenados[4],  # VehiculosZonaE
                        vehiculos_ordenados[5],  # VehiculosZonaF
                        vehiculos_ordenados[6],  # VehiculosZonaG
                        vehiculos_ordenados[7],  # VehiculosZonaH
                        vehiculos_ordenados[8],  # VehiculosZonaI
                        vehiculos_ordenados[9],  # VehiculosZonaJ
                        vehiculos_ordenados[10],  # VehiculosZonaK
                        vehiculos_ordenados[11],  # VehiculosZonaL
                        data.generated_at,
                    ),
                )
                print("++++++++++++++++++++++++++++++++++++++++++++++++++6")

                if not self._db_connection:
                    print("++++++++++++++++++++++++++++++++++++++++++++++++++7")
                    return False
                else:
                    print("++++++++++++++++++++++++++++++++++++++++++++++++++9")
                    self._db_connection.commit()
                    print("++++++++++++++++++++++++++++++++++++++++++++++++++10")
                    return True
        except Exception as e:
            logger.error(f"❌ Error al guardar el reporte en la base de datos: {e}")
            return False

    def _check_and_alert(self, data: ReportData) -> None:
        """
        Revisa si se tiene que generar alguna alerta. Condiciones:
        - Tiempo de espera total mayor al tiempo de espera máximo permitido.
        - Tiempo de espera de una zona mayor al tiempo de espera máximo permitido.

        Args:
            data (ReportData): Datos validados de la simulación.
        """
        tiempo_espera_total = data.get_tiempo_espera_total()

        if tiempo_espera_total > self.settings.tiempo_total_espera_maximo:
            self.logger.warning(
                f"⚠️ Step {data.steps}: Tiempo de espera total mayor al permitido ({tiempo_espera_total})."
            )

        for i, zone_wait_time in enumerate(data.tiempos_espera):
            if zone_wait_time > self.settings.tiempo_zona_espera_maximo:
                max_wait_zone_name = chr(ord("A") + i)  #! Convertir índice a letra
                self.logger.warning(
                    f"⚠️ Step {data.steps}: Tiempo de espera en la zona {max_wait_zone_name} mayor permitido ({zone_wait_time})."
                )
