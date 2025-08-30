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
    def __init__(self) -> None:
        logging.basicConfig(level=logging.DEBUG)
        self.report_service = ReportService()

    def generate_report(self) -> None:
        """
        Generar reporte.
        """
        logger = logging.getLogger("ReportApp")
        logger.info("Iniciando generacion de reporte...")
        self.report_service.generate_report()
