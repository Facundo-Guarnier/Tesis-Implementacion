# --- Modelos para la sección 'deteccion' ---
from pydantic import BaseModel


class DeteccionCarpetaSettings(BaseModel):
    procesar: bool  #! Procesar todos los videos de la carpeta del dataset
    path_origen: str  #! Carpeta con los videos a procesar
    path_destino: str  #! Carpeta donde se guardarán los resultados


class DeteccionUnVideoSettings(BaseModel):
    procesar: bool  #! Procesar un video en específico
    guardar: bool  #! Guardar el video con los resultados
    path_origen: str  #! Path del video a procesar
    zona: str  #! Zona a considerar
    path_destino: str  #! Carpeta donde se guardará el video con los resultados


class DeteccionSettings(BaseModel):
    detectar: bool  # * Iniciar la detección de objetos
    modelo: str  #! Modelo de detección de objetos
    carpeta_dataset: DeteccionCarpetaSettings
    un_video: DeteccionUnVideoSettings
    procesar_camara: bool  #! Procesar la cámara en tiempo real


# --- Modelos para la sección 'decision' ---
class EntrenamientoSettings(BaseModel):
    entrenar: bool  # * Entrenar el modelo
    path_resultado: str  #! Carpeta donde se guardarán los resultados del entrenamiento
    num_epocas: int
    batch_size: int
    steps: int
    memory: int
    learning_rate: float
    learning_rate_decay: float
    learning_rate_min: float
    epsilon: float
    epsilon_decay: float
    epsilon_min: float
    gamma: float
    hidden_layers: list[int]


class DecisionSettings(BaseModel):
    decision: bool  # * Iniciar la toma de decisiones
    ponderaciones_zonas: list[float]  #! Ponderaciones de las zonas
    path_modelo_entrenado: str
    entrenamiento: EntrenamientoSettings


# --- Modelos para 'sumo' y 'reporte' ---
class SumoSettings(BaseModel):
    simular: bool  # * Iniciar la simulación en SUMO
    gui: bool  #! Mostrar la interfaz gráfica de SUMO
    comparar: bool  #! Comparar la simulación con la detección de objetos
    path_sumo: str  #! Path de la instalación de SUMO


class ReporteSettings(BaseModel):
    generar: bool  # * Generar el reporte de la simulación
    path_reporte: str  #! Carpeta donde se guardará el reporte
    steps: int  #! Número de pasos a considerar entre cada reporte
    tiempo_total_espera_maximo: int  #! Tiempo de espera máximo en segundos en total
    tiempo_zona_espera_maximo: int  #! Tiempo de espera máximo en segundos por zona
    tiempo_entre_reportes: (
        int  #! Tiempo entre cada intento fallado de reporte en segundos
    )


# --- La Clase Principal de Configuración ---
class AppSettings(BaseModel):
    base_url: str  #! URL base del servidor Flask
    deteccion: DeteccionSettings
    decision: DecisionSettings
    sumo: SumoSettings
    reporte: ReporteSettings
