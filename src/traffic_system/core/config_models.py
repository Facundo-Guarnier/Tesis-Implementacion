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

    # === NUEVAS CONFIGURACIONES ANTI-GRADIENT VANISHING ===
    use_batch_normalization: bool = True  # * Batch Normalization entre capas
    use_he_initialization: bool = True  # * He initialization para ReLU
    use_residual_connections: bool = True  # * Skip connections para redes profundas
    gradient_clip_norm: float = 1.0  # * Norma máxima para gradient clipping
    use_leaky_relu: bool = True  # * LeakyReLU en lugar de ReLU estándar

    # Configuración adicional para estabilidad
    use_gradient_clipping: bool = True  # * Gradient clipping activado
    use_huber_loss: bool = True  # * Huber Loss más robusto que MSE
    normalize_rewards: bool = True  # * Normalización de recompensas

    # FASE 4: Evaluación y métricas
    enable_evaluation: bool = True  # * Activar sistema de evaluación
    evaluation_episodes: int = 10  # * Número de episodios para evaluación
    evaluation_frequency: int = 5  # * Evaluar cada N épocas
    baseline_comparison: bool = True  # * Comparar con modelo baseline
    save_evaluation_data: bool = True  # * Guardar datos de evaluación
    metrics_window_size: int = 100  # * Ventana para métricas deslizantes
    statistical_tests: bool = True  # * Realizar pruebas estadísticas
    generate_plots: bool = True  # * Generar gráficos de progreso

    # ESTABILIDAD DEL ENTRENAMIENTO
    warmup_steps: int = 250  # * Pasos de simulación a omitir al inicio de cada época
    min_replay_size: int = (
        32  # * Mínimo de experiencias para empezar entrenamiento (batch dinámico)
    )

    # OPTIMIZACIONES DE RENDIMIENTO (Bajo Riesgo)
    enable_jit_compilation: bool = True  # * Activar XLA/JIT para optimización GPU
    dropout_mode: str = "optimized"  # * "full", "optimized", "minimal"
    dropout_layers: str = "strategic"  # * "all_layers", "strategic", "output_only"
    noisy_implementation: str = "efficient"  # * "gaussian_noise", "efficient"

    # OPTIMIZACIONES AVANZADAS (Riesgo Moderado)
    # Double DQN Optimization
    double_dqn_batch_optimization: bool = (
        False  # * Procesar actualizaciones target en lotes
    )
    target_update_batch_size: int = 512  # * Tamaño del lote para actualizaciones target

    # Prioritized Experience Replay Optimization
    per_batch_processing: bool = False  # * Procesar TD-errors en lotes más grandes
    per_update_frequency: int = (
        4  # * Actualizar prioridades cada N steps (no cada step)
    )
    per_importance_annealing: bool = (
        False  # * Annealing automático de importance sampling
    )

    # Architecture Simplification
    dueling_stream_simplification: bool = False  # * Simplificar streams de Dueling DQN
    hidden_layers_optimization: bool = (
        False  # * Optimizar número de capas automáticamente
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
