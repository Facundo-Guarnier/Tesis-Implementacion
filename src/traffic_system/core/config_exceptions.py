class ConfigValidationError(Exception):
    """Excepción lanzada cuando hay un error en la validación del archivo de configuración."""

    def __init__(self, message: str):
        self.message: str = message
        super().__init__(self.message)
