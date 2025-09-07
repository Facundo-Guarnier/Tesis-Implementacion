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
        logger = logging.getLogger("ReportService")

        #! Verificar si la simulación fue exitosa
        while not self._client_api_report.is_simulation_running():
            time.sleep(1)

        self._connect_db()
        self._create_table()

        #! Generar reporte basado en umbrales de congestión
        # Nota: Configuración de steps mantenida para uso futuro

        while True:
            data = self._get_data()
            if data is None:
                logger.error("Error al obtener datos del reporte. Reintentando...")
                time.sleep(5)
                continue

            # Evaluar si algún umbral crítico se supera (condiciones de congestión)
            should_save = self._evaluate_thresholds(data)

            if should_save:
                if self._save_report(data=data):
                    self._check_and_alert(data=data)
                else:
                    logger.error(f"Error al guardar el reporte para step {data.steps}")

            # Esperar un poco antes de verificar nuevamente
            time.sleep(1)  # 1 segundo entre verificaciones

        # logger.error("❌ Falló 5 veces seguidas al intentar generar el reporte.")
        # self._close_db()

    def _create_logger(self) -> None:
        """
        Crea un logger para registrar las alertas en un archivo .log.
        """
        self.logger = logging.getLogger("ReportService")
        self.logger.setLevel(logging.INFO)

        log_dir = os.path.join(self._report_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        #! Crear un manejador de archivos con encoding UTF-8
        file_handler = logging.FileHandler(
            os.path.join(self._report_path, "alertas.log"),
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)

        #! Crear un formateador simplificado sin el nombre largo del modulo
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
        logger = logging.getLogger("ReportService")

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
            logger.debug(
                f"Datos del reporte validados correctamente: steps={validated_data.steps}"
            )
            return validated_data

        except ValidationError as e:
            logger.error(f"Error de validacion en datos del reporte: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al procesar datos del reporte: {e}")
            return None

    def _create_table(self) -> None:
        """
        Crea la tabla en la base de datos SQLite si no existe.
        """
        sql = """
            CREATE TABLE IF NOT EXISTS reporte (
                step_simulacion INTEGER PRIMARY KEY,
                estado_simulacion TEXT,
                timestamp_simulacion TEXT,
                estado_semaforo_1 TEXT,
                estado_semaforo_2 TEXT,
                estado_semaforo_3 TEXT,
                estado_semaforo_4 TEXT,
                total_tiempo_espera REAL,
                total_vehiculos INTEGER,
                zona_a_tiempo_espera REAL,
                zona_a_vehiculos INTEGER,
                zona_b_tiempo_espera REAL,
                zona_b_vehiculos INTEGER,
                zona_c_tiempo_espera REAL,
                zona_c_vehiculos INTEGER,
                zona_d_tiempo_espera REAL,
                zona_d_vehiculos INTEGER,
                zona_e_tiempo_espera REAL,
                zona_e_vehiculos INTEGER,
                zona_f_tiempo_espera REAL,
                zona_f_vehiculos INTEGER,
                zona_g_tiempo_espera REAL,
                zona_g_vehiculos INTEGER,
                zona_h_tiempo_espera REAL,
                zona_h_vehiculos INTEGER,
                zona_i_tiempo_espera REAL,
                zona_i_vehiculos INTEGER,
                zona_j_tiempo_espera REAL,
                zona_j_vehiculos INTEGER,
                zona_k_tiempo_espera REAL,
                zona_k_vehiculos INTEGER,
                zona_l_tiempo_espera REAL,
                zona_l_vehiculos INTEGER,
                generado_en TEXT
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
            sql = """
                INSERT OR REPLACE INTO reporte (
                    step_simulacion, estado_simulacion, timestamp_simulacion,
                    estado_semaforo_1, estado_semaforo_2, estado_semaforo_3, estado_semaforo_4,
                    total_tiempo_espera, total_vehiculos,
                    zona_a_tiempo_espera, zona_a_vehiculos,
                    zona_b_tiempo_espera, zona_b_vehiculos,
                    zona_c_tiempo_espera, zona_c_vehiculos,
                    zona_d_tiempo_espera, zona_d_vehiculos,
                    zona_e_tiempo_espera, zona_e_vehiculos,
                    zona_f_tiempo_espera, zona_f_vehiculos,
                    zona_g_tiempo_espera, zona_g_vehiculos,
                    zona_h_tiempo_espera, zona_h_vehiculos,
                    zona_i_tiempo_espera, zona_i_vehiculos,
                    zona_j_tiempo_espera, zona_j_vehiculos,
                    zona_k_tiempo_espera, zona_k_vehiculos,
                    zona_l_tiempo_espera, zona_l_vehiculos,
                    generado_en
                )
                VALUES (
                    :step_simulacion, :estado_simulacion, :timestamp_simulacion,
                    :estado_semaforo_1, :estado_semaforo_2, :estado_semaforo_3, :estado_semaforo_4,
                    :total_tiempo_espera, :total_vehiculos,
                    :zona_a_tiempo_espera, :zona_a_vehiculos,
                    :zona_b_tiempo_espera, :zona_b_vehiculos,
                    :zona_c_tiempo_espera, :zona_c_vehiculos,
                    :zona_d_tiempo_espera, :zona_d_vehiculos,
                    :zona_e_tiempo_espera, :zona_e_vehiculos,
                    :zona_f_tiempo_espera, :zona_f_vehiculos,
                    :zona_g_tiempo_espera, :zona_g_vehiculos,
                    :zona_h_tiempo_espera, :zona_h_vehiculos,
                    :zona_i_tiempo_espera, :zona_i_vehiculos,
                    :zona_j_tiempo_espera, :zona_j_vehiculos,
                    :zona_k_tiempo_espera, :zona_k_vehiculos,
                    :zona_l_tiempo_espera, :zona_l_vehiculos,
                    :generado_en
                );
            """
            logger = logging.getLogger("ReportService")
            if not self._cursor:
                return False
            else:
                # Usar los métodos del modelo para obtener datos estructurados
                vehiculos_ordenados = data.get_vehiculos_ordenados()
                tiempo_espera_total = data.get_tiempo_espera_total()
                total_vehiculos = data.get_total_vehiculos()

                # Usar diccionario con parámetros nombrados para mejor legibilidad y mantenibilidad
                params = {
                    # Información básica de simulación
                    "step_simulacion": data.steps,
                    "estado_simulacion": data.status,
                    "timestamp_simulacion": data.timestamp,
                    # Estados de semáforos
                    "estado_semaforo_1": data.estados_semaforos[0],
                    "estado_semaforo_2": data.estados_semaforos[1],
                    "estado_semaforo_3": data.estados_semaforos[2],
                    "estado_semaforo_4": data.estados_semaforos[3],
                    # Totales
                    "total_tiempo_espera": tiempo_espera_total,
                    "total_vehiculos": total_vehiculos,
                    # Zonas A-F
                    "zona_a_tiempo_espera": data.tiempos_espera[0],
                    "zona_a_vehiculos": vehiculos_ordenados[0],
                    "zona_b_tiempo_espera": data.tiempos_espera[1],
                    "zona_b_vehiculos": vehiculos_ordenados[1],
                    "zona_c_tiempo_espera": data.tiempos_espera[2],
                    "zona_c_vehiculos": vehiculos_ordenados[2],
                    "zona_d_tiempo_espera": data.tiempos_espera[3],
                    "zona_d_vehiculos": vehiculos_ordenados[3],
                    "zona_e_tiempo_espera": data.tiempos_espera[4],
                    "zona_e_vehiculos": vehiculos_ordenados[4],
                    "zona_f_tiempo_espera": data.tiempos_espera[5],
                    "zona_f_vehiculos": vehiculos_ordenados[5],
                    # Zonas G-L
                    "zona_g_tiempo_espera": data.tiempos_espera[6],
                    "zona_g_vehiculos": vehiculos_ordenados[6],
                    "zona_h_tiempo_espera": data.tiempos_espera[7],
                    "zona_h_vehiculos": vehiculos_ordenados[7],
                    "zona_i_tiempo_espera": data.tiempos_espera[8],
                    "zona_i_vehiculos": vehiculos_ordenados[8],
                    "zona_j_tiempo_espera": data.tiempos_espera[9],
                    "zona_j_vehiculos": vehiculos_ordenados[9],
                    "zona_k_tiempo_espera": data.tiempos_espera[10],
                    "zona_k_vehiculos": vehiculos_ordenados[10],
                    "zona_l_tiempo_espera": data.tiempos_espera[11],
                    "zona_l_vehiculos": vehiculos_ordenados[11],
                    # Metadata
                    "generado_en": data.generated_at,
                }

                self._cursor.execute(sql, params)

                if not self._db_connection:
                    return False
                else:
                    self._db_connection.commit()
                    return True
        except Exception as e:
            logger.error(f"Error al guardar el reporte en la base de datos: {e}")
            return False

    def _evaluate_thresholds(self, data: ReportData) -> bool:
        """
        Evalua si algun umbral critico de congestion se supera.
        Retorna True solo si se debe guardar el reporte (umbral superado).

        Args:
            data (ReportData): Datos validados de la simulacion.

        Returns:
            bool: True si se debe guardar el reporte (umbral superado), False en caso contrario.
        """
        # 1. Verificar tiempo total de espera
        tiempo_espera_total = data.get_tiempo_espera_total()
        if tiempo_espera_total >= self.settings.tiempo_total_espera_maximo:
            return True

        # 2. Verificar tiempo de espera por zona
        for zone_wait_time in data.tiempos_espera:
            if zone_wait_time >= self.settings.tiempo_zona_espera_maximo:
                return True

        # 3. Verificar total de vehiculos
        total_vehiculos = data.get_total_vehiculos()
        if total_vehiculos >= self.settings.total_vehiculos_maximo:
            return True

        # 4. Verificar cantidad de vehiculos por zona
        vehiculos_ordenados = data.get_vehiculos_ordenados()
        for zone_vehicles in vehiculos_ordenados:
            if zone_vehicles >= self.settings.zona_vehiculos_maximo:
                return True

        # Ningun umbral superado - condiciones normales
        return False

    def _check_and_alert(self, data: ReportData) -> None:
        """
        Revisa y registra alertas cuando se superan umbrales especificos.
        Solo registra logs cuando se detectan condiciones criticas.

        Args:
            data (ReportData): Datos validados de la simulacion.
        """
        # Definir nombres de zonas para logs más claros
        zone_names = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]

        # 1. Verificar tiempo total de espera
        tiempo_espera_total = data.get_tiempo_espera_total()
        if tiempo_espera_total > self.settings.tiempo_total_espera_maximo:
            self.logger.warning(
                f"{data.steps}: Tiempo total espera SUPERADO - "
                f"Valor: {tiempo_espera_total:.1f}s | Umbral: {self.settings.tiempo_total_espera_maximo}s"
            )

        # 2. Verificar tiempo de espera por zona
        for i, zone_wait_time in enumerate(data.tiempos_espera):
            if zone_wait_time > self.settings.tiempo_zona_espera_maximo:
                zone_name = zone_names[i]
                self.logger.warning(
                    f"{data.steps}: Zona {zone_name} tiempo espera SUPERADO - "
                    f"Valor: {zone_wait_time:.1f}s | Umbral: {self.settings.tiempo_zona_espera_maximo}s"
                )

        # 3. Verificar total de vehiculos
        total_vehiculos = data.get_total_vehiculos()
        if total_vehiculos > self.settings.total_vehiculos_maximo:
            self.logger.warning(
                f"{data.steps}: Total vehiculos SUPERADO - "
                f"Valor: {total_vehiculos} | Umbral: {self.settings.total_vehiculos_maximo}"
            )

        # 4. Verificar cantidad de vehiculos por zona
        vehiculos_ordenados = data.get_vehiculos_ordenados()
        for i, zone_vehicles in enumerate(vehiculos_ordenados):
            if zone_vehicles > self.settings.zona_vehiculos_maximo:
                zone_name = zone_names[i]
                self.logger.warning(
                    f"{data.steps}: Zona {zone_name} vehiculos SUPERADO - "
                    f"Valor: {zone_vehicles} | Umbral: {self.settings.zona_vehiculos_maximo}"
                )
