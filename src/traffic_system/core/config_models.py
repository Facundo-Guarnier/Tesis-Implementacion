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

    # FASE 2: Mejoras algorítmicas DQN
    use_double_dqn: bool = True  # * Activar Double DQN (reduce sobreestimación)
    use_dueling_dqn: bool = True  # * Activar Dueling DQN (separar valor y ventaja)
    target_update_frequency: int = 100  # * Frecuencia de actualización red target

    # FASE 3: Optimizaciones avanzadas
    use_prioritized_replay: bool = True  # * Activar Prioritized Experience Replay (PER)
    per_alpha: float = 0.6  # * Priorización exponent (0=uniform, 1=full priority)
    per_beta_start: float = 0.4  # * Importance sampling beta inicial
    per_beta_frames: int = 100000  # * Frames para llegar a beta=1.0
    use_noisy_networks: bool = True  # * Activar Noisy Networks para exploración
    noise_std: float = 0.5  # * Desviación estándar del ruido
    use_dropout: bool = True  # * Activar Dropout para regularización
    dropout_rate: float = 0.1  # * Tasa de dropout
    adaptive_lr: bool = True  # * Learning rate adaptativo
    lr_schedule_type: str = (
        "cosine"  # * Tipo de schedule: "exponential", "cosine", "plateau"
    )


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
    simulation_time_limit: int


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
