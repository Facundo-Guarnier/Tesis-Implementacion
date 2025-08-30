# --- Modelos para la sección 'deteccion' ---

from pydantic import BaseModel, field_validator


# --- Modelos para datos del reporte ---
class ReportData(BaseModel):
    """Modelo para los datos del reporte de simulación."""

    status: str
    timestamp: str | None
    steps: int
    tiempos_espera: list[float]
    cantidad_vehiculos_por_zona: dict[str, int]
    estados_semaforos: list[str]
    generated_at: str

    @field_validator("tiempos_espera")
    def validate_tiempos_espera_length(cls, v: list[float]) -> list[float]:
        """Validar que tiempos_espera tenga exactamente 12 elementos (zonas A-L)."""
        if len(v) != 12:
            raise ValueError(
                f"tiempos_espera debe tener 12 elementos, recibido: {len(v)}"
            )
        return v

    @field_validator("cantidad_vehiculos_por_zona")
    def validate_cantidad_vehiculos_zonas(cls, v: dict[str, int]) -> dict[str, int]:
        """Validar que cantidad_vehiculos_por_zona tenga las zonas A-L."""
        expected_zones = {chr(ord("A") + i) for i in range(12)}
        received_zones = set(v.keys())
        if received_zones != expected_zones:
            missing = expected_zones - received_zones
            extra = received_zones - expected_zones
            error_msg = []
            if missing:
                error_msg.append(f"Faltan zonas: {sorted(missing)}")
            if extra:
                error_msg.append(f"Zonas extra: {sorted(extra)}")
            raise ValueError(f"Zonas incorrectas. {', '.join(error_msg)}")
        return v

    @field_validator("estados_semaforos")
    def validate_estados_semaforos_length(cls, v: list[str]) -> list[str]:
        """Validar que estados_semaforos tenga exactamente 4 elementos."""
        if len(v) != 4:
            raise ValueError(
                f"estados_semaforos debe tener 4 elementos, recibido: {len(v)}"
            )
        return v

    def get_tiempo_espera_total(self) -> float:
        """Calcular el tiempo de espera total."""
        return sum(self.tiempos_espera)

    def get_vehiculos_ordenados(self) -> list[int]:
        """Obtener lista de vehículos ordenada por zona A-L."""
        return [self.cantidad_vehiculos_por_zona[chr(ord("A") + i)] for i in range(12)]

    def get_total_vehiculos(self) -> int:
        """Calcular el total de vehículos en todas las zonas."""
        return sum(self.cantidad_vehiculos_por_zona.values())


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
    path_resultados_deteccion: (
        str  #! Carpeta donde se guardan los resultados de detección automática
    )
    # Opciones de visualización/rotación (valores por defecto para no romper config existente)
    forced_rotation_degrees: int = 0  # 0, 90, 180, 270
    window_fixed: bool = True
    window_size: list[int] = [460, 820]  # [ancho, alto]


# --- Modelos para la sección 'decision' ---
class EntrenamientoSimplificadoSettings(BaseModel):
    """Configuración simplificada para entrenamiento DQN - configuración básica y estable."""

    entrenar: bool  # * Entrenar el modelo con configuración simplificada
    path_resultado: str  #! Carpeta donde se guardarán los resultados del entrenamiento

    # === HIPERPARÁMETROS BÁSICOS ===
    num_epocas: int  #! Suficientes épocas para ver tendencias claras
    batch_size: int  #! Tamaño de lote estándar
    steps: int  #! Pasos de simulación por acción
    memory: int  #! Buffer de experiencias más grande para diversidad
    min_replay_size: int  #! Mínimo para empezar entrenamiento (batch dinámico)

    # === OPTIMIZACIÓN Y LEARNING RATE ===
    learning_rate: float  #! Punto de partida conservador y seguro

    # === EXPLORACIÓN - SOLO EPSILON GREEDY ===
    epsilon: float  #! 100% exploración inicial
    epsilon_decay: float  #! Decay lento para explorar durante más tiempo
    epsilon_min: float  #! 10% exploración mínima

    # === DESCUENTO Y ARQUITECTURA ===
    gamma: float  #! Valor estándar que mira al futuro
    hidden_layers: list[int]  #! Red simple pero más potente

    # === MEJORAS ALGORÍTMICAS DQN - SOLO LAS PROBADAS ===
    use_double_dqn: bool = True  #! Técnica probada y estable
    use_dueling_dqn: bool = True  #! Técnica probada y estable
    target_update_frequency: int = 200  #! Valor estándar y estable

    # === ESTABILIDAD DEL ENTRENAMIENTO ===
    warmup_steps: int  #! Pasos de calentamiento para estabilizar la simulación
    use_gradient_clipping: bool = True  #! Previene gradient explosion
    gradient_clip_norm: float = 0.8  #! Valor estándar
    use_huber_loss: bool = True  #! Más robusto que MSE
    use_he_initialization: bool = True  #! Segura y estándar

    # === EVALUACIÓN ===
    enable_evaluation: bool = True  #! Importante para monitoreo
    evaluation_episodes: int = 10  #! Episodios de evaluación
    evaluation_frequency: int = 5  #! Evaluar cada 5 épocas

    # === EARLY STOPPING ===
    patience: int = 10  #! Épocas sin mejora antes de parar
    min_improvement: float = 0.01  #! Mejora mínima requerida


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
    steps: int = 15  #! Pasos de simulación por acción del agente
    entrenamiento_simplificado: EntrenamientoSimplificadoSettings
    entrenamiento_completo: EntrenamientoSettings


# --- Modelos para 'sumo' y 'reporte' ---
class SumoSettings(BaseModel):
    simular: bool  # * Iniciar la simulación en SUMO
    gui: bool  #! Mostrar la interfaz gráfica de SUMO
    comparar: bool  #! Comparar la simulación con la detección de objetos
    path_sumo: str  #! Path de la instalación de SUMO
    path_mapa: str  #! Ruta del archivo de configuración del mapa SUMO (.sumocfg)
    simulation_time_limit: int

    # === CONFIGURACIÓN DE SEMILLAS ALEATORIAS ===
    use_random_seed: bool = (
        False  # * Usar semilla aleatoria (tiempo actual del sistema)
    )
    fixed_seed: int | None = (
        None  # * Semilla fija específica (None = usar default de SUMO: 23423)
    )
    persist_random_seed: bool = (
        True  # * Si use_random_seed=True: reutilizar misma semilla en reinicios (True) o generar nueva cada vez (False)
    )


class ReporteSettings(BaseModel):
    """Configuración del servicio de reportes de tráfico."""

    # Configuración legacy del sistema anterior
    generar: bool  # * Generar el reporte de la simulación
    path_reporte: str  #! Carpeta donde se guardará el reporte
    steps: int  #! Número de pasos a considerar entre cada reporte
    tiempo_total_espera_maximo: int  #! Tiempo de espera máximo en segundos en total
    tiempo_zona_espera_maximo: int  #! Tiempo de espera máximo en segundos por zona
    total_vehiculos_maximo: int
    zona_vehiculos_maximo: int
    db_path_base: str


class ServicesSettings(BaseModel):
    """Configuración de los servicios del sistema de tráfico."""

    simulation_port: int = 5000
    detection_port: int = 5000
    reporting_port: int = 5001


# --- La Clase Principal de Configuración ---
class AppSettings(BaseModel):
    base_url: str  #! URL base del servidor Flask
    base_ip: str
    services: ServicesSettings
    deteccion: DeteccionSettings
    decision: DecisionSettings
    sumo: SumoSettings
    reporte: ReporteSettings
