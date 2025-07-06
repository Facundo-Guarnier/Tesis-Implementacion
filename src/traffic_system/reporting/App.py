import inspect
import logging

from src.traffic_system.reporting.report_service import ReportService

# [CU1]
# Esta seccion le pide información a la API de deteccion y de simulacion para
# obtener los datos de flujo vehicular y mostrarselos al agente de transito, ya
# sea en un csv o de otra manera.
#
# [CU2]
# En base a la información obtenida se pueden realizar las alertas correspondientes
# para el segundo caso de usuario.


class ReportApp:
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.reporte = ReportService()

    def generate_report(self) -> None:
        """
        Generar reporte.
        """
        logger = logging.getLogger(
            f" {self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"  # type: ignore
        )
        logger.info("📄 Iniciando generación de reporte...")
        self.reporte.main()
