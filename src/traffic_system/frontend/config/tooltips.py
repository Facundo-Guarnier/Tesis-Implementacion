"""
Configuración de tooltips para los campos del frontend.

Este archivo contiene las descripciones y ayudas contextuales para todos los campos
de configuración del sistema de semáforos inteligentes, organizados por categorías.
"""

# Diccionario de tooltips basado en comentarios del config.yaml
CONFIG_TOOLTIPS: dict[str, str] = {
    # Configuración global
    "base_url": "URL base del servidor Flask: dirección completa donde se expondrán las APIs REST (ej: http://localhost:5000)",
    "base_ip": "Dirección IP base: IP donde escucharán los servicios. 127.0.0.1 = solo local, 0.0.0.0 = todas las interfaces de red",
    # Servicios
    "services.simulation_port": "Puerto para API de simulación SUMO: donde se expone el control de la simulación de tráfico (típicamente 5000)",
    "services.detection_port": "Puerto para API de detección YOLO: donde se expone el servicio de detección de vehículos (típicamente 5001)",
    "services.reporting_port": "Puerto para API de reportes: donde se exponen métricas y estadísticas post-simulación (típicamente 5002)",
    # Detección
    "deteccion.detectar": "Activar detección de objetos: iniciar el procesamiento de video con YOLO para detectar vehículos en tiempo real",
    "deteccion.modelo": "Modelo YOLO: versión del modelo de detección. yolov8n.pt = nano (rápido), yolov8s.pt = small, yolov8m.pt = medium (más preciso)",
    "deteccion.path_resultados_deteccion": "Directorio de resultados: carpeta donde se guardan videos procesados, imágenes con detecciones y archivos CSV con estadísticas",
    "deteccion.forced_rotation_degrees": "Rotación forzada: rotar frames del video. 0° = sin rotación, 90° = sentido horario, 180° = voltear, 270° = anti-horario",
    "deteccion.window_fixed": "Ventana fija: True = tamaño constante de ventana, False = ventana se redimensiona automáticamente según contenido",
    "deteccion.window_size": "Tamaño de ventana: [ancho, alto] en píxeles para mostrar el video procesado. [460, 820] = formato vertical típico",
    # Detección - Carpeta dataset
    "deteccion.carpeta_dataset.procesar": "Procesar todos los videos de la carpeta del dataset",
    "deteccion.carpeta_dataset.path_origen": "Carpeta con los videos a procesar",
    "deteccion.carpeta_dataset.path_destino": "Carpeta donde se guardarán los resultados",
    # Detección - Un video
    "deteccion.un_video.procesar": "Procesar un video en específico",
    "deteccion.un_video.guardar": "Guardar el video con los resultados de detección",
    "deteccion.un_video.zona": "Zona de detección para el video",
    "deteccion.un_video.path_origen": "Ruta del video a procesar. 1080x1920-30fps o 576x1024-5fps",
    "deteccion.un_video.path_destino": "Carpeta donde se guardará el resultado",
    # Detección - Cámara
    "deteccion.procesar_camara": "Procesar la cámara en tiempo real",
    # Decisión
    "decision.decision": "Activar agente de decisión: iniciar el algoritmo de aprendizaje por refuerzo (DQN) para controlar semáforos inteligentemente",
    "decision.path_modelo_entrenado": "Modelo DQN entrenado: ruta del archivo .h5 o .keras con los pesos de la red neuronal ya entrenada para inferencia",
    "decision.steps": "Intervalo de decisión: cada cuántos steps de simulación el agente toma una nueva decisión. 10 = decisiones frecuentes, 20 = menos frecuentes",
    "decision.ponderaciones_zonas": "Pesos por zona: valores de importancia para las 12 zonas de detección. [1.0]*12 = todas iguales, valores mayores = más importantes",
    # Entrenamiento Simplificado
    "decision.entrenamiento_simplificado.entrenar": "Activar entrenamiento DQN simplificado: configuración básica y rápida para pruebas iniciales y aprendizaje del algoritmo.",
    "decision.entrenamiento_simplificado.path_resultado": "Directorio donde se guardan modelos entrenados (.h5/.keras), logs de entrenamiento (.csv) y métricas de evaluación.",
    "decision.entrenamiento_simplificado.num_epocas": "Épocas de entrenamiento: cada época = un episodio completo de simulación. 100 épocas permiten ver tendencias claras de aprendizaje.",
    "decision.entrenamiento_simplificado.batch_size": "Tamaño del lote para entrenamiento: número de experiencias que se procesan juntas. 256 = balance entre estabilidad y velocidad.",
    "decision.entrenamiento_simplificado.steps": "Steps por acción: cuántos pasos de simulación transcurren antes de que el agente tome una nueva decisión. Mayor valor = decisiones menos frecuentes.",
    "decision.entrenamiento_simplificado.memory": "Capacidad del buffer de experiencias: memoria que almacena experiencias (estado, acción, recompensa) para entrenar. 50000 = ~200 épocas de historia.",
    "decision.entrenamiento_simplificado.min_replay_size": "Experiencias mínimas para iniciar entrenamiento: evita entrenar con muy pocos datos. 2000 = suficiente diversidad inicial.",
    "decision.entrenamiento_simplificado.learning_rate": "Tasa de aprendizaje: qué tan rápido cambian los pesos de la red neuronal. 0.001 = conservador y estable, 0.1 = agresivo, 0.00001 = muy lento.",
    "decision.entrenamiento_simplificado.epsilon": "Probabilidad de exploración inicial: 1.0 = 100% acciones aleatorias (exploración total), 0.0 = solo acciones óptimas conocidas.",
    "decision.entrenamiento_simplificado.epsilon_decay": "Factor de reducción de exploración: 0.995 = reduce epsilon gradualmente, 0.9 = reduce rápido, 0.999 = reduce muy lento.",
    "decision.entrenamiento_simplificado.epsilon_min": "Exploración mínima: límite inferior para epsilon. 0.1 = siempre 10% de acciones aleatorias, 0.01 = solo 1% exploración.",
    "decision.entrenamiento_simplificado.gamma": "Factor de descuento: importancia de recompensas futuras. 0.85 = valora futuro cercano, 0.99 = valora futuro lejano, 0.1 = solo presente.",
    "decision.entrenamiento_simplificado.hidden_layers": "Arquitectura de red neuronal: capas ocultas y neuronas por capa. [128, 128] = 2 capas de 128 neuronas cada una.",
    "decision.entrenamiento_simplificado.use_double_dqn": "Double DQN: usa dos redes para evitar sobreestimación de valores Q. True = más estable, False = DQN clásico.",
    "decision.entrenamiento_simplificado.use_dueling_dqn": "Dueling DQN: separa valor del estado y ventaja de acciones. True = mejor para muchas acciones, False = arquitectura estándar.",
    "decision.entrenamiento_simplificado.target_update_frequency": "Frecuencia de actualización de red objetivo: cada cuántos steps se actualiza. 200 = estable, 100 = más dinámico, 500 = muy estable.",
    "decision.entrenamiento_simplificado.warmup_steps": "Steps de calentamiento: pasos iniciales sin entrenamiento para llenar el buffer. 250 = permite que aparezcan vehículos antes de decidir.",
    "decision.entrenamiento_simplificado.use_gradient_clipping": "Recorte de gradientes: previene gradientes explosivos que desestabilizan el entrenamiento. True = más estable.",
    "decision.entrenamiento_simplificado.gradient_clip_norm": "Norma máxima de gradientes: valor límite para recortar gradientes. 0.8 = conservador, 1.0 = estándar, 0.5 = muy restrictivo.",
    "decision.entrenamiento_simplificado.use_huber_loss": "Función de pérdida Huber: más robusta a valores atípicos que MSE. True = menos sensible a errores grandes.",
    "decision.entrenamiento_simplificado.use_he_initialization": "Inicialización He: método óptimo para activaciones ReLU. True = mejores gradientes iniciales.",
    "decision.entrenamiento_simplificado.enable_evaluation": "Activar evaluación periódica: mide rendimiento real sin exploración durante el entrenamiento.",
    "decision.entrenamiento_simplificado.evaluation_episodes": "Episodios de evaluación: cuántas simulaciones completas sin exploración para medir rendimiento real. 10 = estadísticamente suficiente.",
    "decision.entrenamiento_simplificado.evaluation_frequency": "Frecuencia de evaluación: cada cuántas épocas evaluar. 5 = balance entre monitoreo y velocidad de entrenamiento.",
    "decision.entrenamiento_simplificado.patience": "Paciencia para early stopping: épocas sin mejora antes de detener entrenamiento. 10 = evita sobreentrenamiento.",
    "decision.entrenamiento_simplificado.min_improvement": "Mejora mínima requerida: cambio mínimo en métrica para considerar que hay progreso. 0.01 = 1% de mejora mínima.",
    # Entrenamiento Completo
    "decision.entrenamiento_completo.entrenar": "Activar entrenamiento DQN avanzado: configuración completa con técnicas state-of-the-art para máximo rendimiento.",
    "decision.entrenamiento_completo.path_resultado": "Directorio donde se guardan modelos entrenados (.h5/.keras), logs detallados (.csv) y métricas completas de evaluación.",
    # Hiperparámetros básicos
    "decision.entrenamiento_completo.num_epocas": "Épocas de entrenamiento: cada época = episodio completo de simulación. 35 épocas optimizadas para convergencia rápida.",
    "decision.entrenamiento_completo.batch_size": "Tamaño del lote: número de experiencias procesadas juntas. 256 = potencia de 2 óptima para GPU, balance memoria/convergencia.",
    "decision.entrenamiento_completo.steps": "Steps por acción del agente: intervalo entre decisiones. 10 = decisiones frecuentes, 20 = menos frecuentes pero más estables.",
    "decision.entrenamiento_completo.memory": "Buffer de experiencias: 5000 = ~20 épocas de memoria, balance entre diversidad y eficiencia computacional.",
    # Optimización y learning rate
    "decision.entrenamiento_completo.learning_rate": "Tasa de aprendizaje inicial: velocidad de cambio de pesos. 0.0005 = conservador para evitar inestabilidad, 0.001 = estándar, 0.0001 = muy lento.",
    "decision.entrenamiento_completo.learning_rate_decay": "Factor de decay del LR por época: 0.99 = reducción gradual conservadora, 0.95 = más agresiva, 0.999 = muy gradual.",
    "decision.entrenamiento_completo.learning_rate_min": "LR mínimo: límite inferior para mantener aprendizaje. 0.00005 = 10% del LR inicial, evita estancamiento completo.",
    # Exploración epsilon-greedy
    "decision.entrenamiento_completo.epsilon": "Probabilidad inicial de exploración: 1.0 = 100% acciones aleatorias al inicio para explorar todas las posibilidades.",
    "decision.entrenamiento_completo.epsilon_decay": "Factor de decay de epsilon por step: 0.99995 = reducción muy gradual durante todo el entrenamiento para mantener exploración.",
    "decision.entrenamiento_completo.epsilon_min": "Exploración mínima residual: 0.1 = siempre 10% de acciones aleatorias para evitar convergencia prematura.",
    # Descuento y arquitectura
    "decision.entrenamiento_completo.gamma": "Factor de descuento: importancia de recompensas futuras. 0.85 = valora futuro cercano, evita inestabilidad de 0.99.",
    "decision.entrenamiento_completo.hidden_layers": "Arquitectura de red neuronal: [64, 64, 64] = 3 capas de 64 neuronas, menos profunda para evitar gradient vanishing.",
    # Mejoras algorítmicas DQN
    "decision.entrenamiento_completo.use_double_dqn": "Double DQN: reduce sobreestimación de Q-values usando red target separada. True = más estable que DQN clásico.",
    "decision.entrenamiento_completo.use_dueling_dqn": "Dueling DQN: separa valor del estado V(s) y ventaja de acciones A(s,a). True = mejor para problemas con muchas acciones.",
    "decision.entrenamiento_completo.target_update_frequency": "Actualización de red target: cada 100 pasos. Menor = más dinámico, mayor = más estable pero menos responsive.",
    # Estabilidad del entrenamiento
    "decision.entrenamiento_completo.warmup_steps": "Steps de calentamiento: pasos iniciales sin entrenamiento. 250 = espera a que lleguen vehículos desde spawn points.",
    "decision.entrenamiento_completo.min_replay_size": "Experiencias mínimas para entrenar: 32 = batch dinámico que crece hasta 256, evita entrenar con muy pocos datos.",
    "decision.entrenamiento_completo.use_gradient_clipping": "Recorte de gradientes: previene gradientes explosivos. True = clipnorm=1.0, entrenamiento más estable.",
    "decision.entrenamiento_completo.use_huber_loss": "Función de pérdida Huber: más robusta a outliers que MSE. True = menos sensible a errores grandes.",
    "decision.entrenamiento_completo.normalize_rewards": "Normalización de recompensas: escala recompensas para estabilidad numérica. True = mejores gradientes.",
    # Prioritized Experience Replay (PER)
    "decision.entrenamiento_completo.use_prioritized_replay": "Prioritized Experience Replay: entrena más con experiencias 'sorprendentes' (alto TD-error). True = aprendizaje más eficiente.",
    "decision.entrenamiento_completo.per_alpha": "Exponente de priorización PER: 0.0 = uniforme (sin prioridad), 1.0 = totalmente priorizado, 0.6 = balance óptimo.",
    "decision.entrenamiento_completo.per_beta_start": "Importance sampling inicial: corrige sesgo de PER. 0.4 = inicio conservador, crece hasta 1.0 para corrección completa.",
    "decision.entrenamiento_completo.per_beta_frames": "Steps para beta=1.0: tiempo para corrección completa de sesgo PER. 100000 = crecimiento gradual durante entrenamiento.",
    # Noisy Networks
    "decision.entrenamiento_completo.use_noisy_networks": "Noisy Networks: exploración mediante ruido en pesos de la red. True = reemplaza epsilon-greedy, exploración más inteligente.",
    "decision.entrenamiento_completo.noise_std": "Desviación estándar del ruido: intensidad del ruido paramétrico. 0.3 = balance entre exploración y estabilidad.",
    # Regularización
    "decision.entrenamiento_completo.use_dropout": "Dropout: previene overfitting desactivando neuronas aleatoriamente durante entrenamiento. True = mejor generalización.",
    "decision.entrenamiento_completo.dropout_rate": "Tasa de dropout: fracción de neuronas desactivadas. 0.02 = 2% muy suave para redes menos profundas.",
    # Learning Rate Adaptativo
    "decision.entrenamiento_completo.adaptive_lr": "Learning Rate Scheduling: ajusta LR según progreso. True = plateau detection, reduce LR cuando se estanca.",
    # Configuraciones anti-gradient vanishing
    "decision.entrenamiento_completo.use_batch_normalization": "Batch Normalization: normaliza entradas de cada capa. True = gradientes más estables, entrena más rápido.",
    "decision.entrenamiento_completo.use_he_initialization": "He Initialization: inicialización óptima para ReLU. True = mejores gradientes iniciales, convergencia más rápida.",
    "decision.entrenamiento_completo.use_residual_connections": "Residual Connections: skip connections para redes profundas. True = evita gradient vanishing en redes complejas.",
    "decision.entrenamiento_completo.gradient_clip_norm": "Norma de recorte de gradientes: límite máximo para gradientes. 1.0 = estándar, 0.5 = más restrictivo.",
    "decision.entrenamiento_completo.use_leaky_relu": "LeakyReLU: evita 'dying ReLU' problem. True = α=0.01, permite pequeños gradientes en valores negativos.",
    # Evaluación y métricas
    "decision.entrenamiento_completo.enable_evaluation": "Sistema de evaluación: mide progreso real del modelo sin exploración durante entrenamiento.",
    "decision.entrenamiento_completo.evaluation_episodes": "Episodios de evaluación: simulaciones completas sin exploración para medir rendimiento real. 10 = estadísticamente suficiente.",
    "decision.entrenamiento_completo.evaluation_frequency": "Frecuencia de evaluación: cada 10 épocas para balance entre monitoreo y velocidad de entrenamiento.",
    "decision.entrenamiento_completo.baseline_comparison": "Comparación con baseline: mide rendimiento vs modelo aleatorio o rule-based. True = contexto de mejora.",
    "decision.entrenamiento_completo.save_evaluation_data": "Guardar datos de evaluación: métricas históricas para análisis posterior. True = CSV con progreso temporal.",
    # SUMO
    "sumo.simular": "Activar simulación SUMO: iniciar la simulación de tráfico con el simulador microscópico para entrenar o evaluar el agente",
    "sumo.gui": "Interfaz gráfica SUMO: True = mostrar ventana visual de simulación, False = modo headless (más rápido, para servidores)",
    "sumo.comparar": "Modo comparación: contrastar rendimiento del control RL vs detección YOLO vs semáforos fijos para evaluar mejoras",
    "sumo.path_sumo": "Directorio de instalación SUMO: ruta donde está instalado SUMO. Linux: /usr/share/sumo, Windows: C:\\sumo o similar",
    "sumo.vehicle_scale": "Escalado de vehículos: factor multiplicador aplicado cuando comparar=True y gui=True. 1.0=normal, 1.25=+25% vehículos",
    "sumo.simulation_time_limit": "Límite temporal: duración máxima de simulación en segundos. 19500s ≈ 5.4 horas de simulación virtual",
    "sumo.fixed_seed": "Semilla específica: valor fijo para reproducibilidad exacta. null = usar default SUMO (23423), número = semilla custom",
    "sumo.use_random_seed": "Semilla aleatoria: True = generar semilla basada en tiempo actual, False = usar fixed_seed o default SUMO",
    "sumo.persist_random_seed": "Persistir semilla: si use_random_seed=True, reutilizar misma semilla en reinicios (True) o generar nueva cada vez (False)",
    # Exportación de comparaciones
    "sumo.comparacion_export.enabled": "Activar exportación: guardar métricas comparativas DQN vs Tiempos Fijos en directorios únicos con timestamp",
    "sumo.comparacion_export.db_path": "Ruta base: cada simulación creará comparison_YYYY-MM-DD_HH-MM-SS/comparison.db automáticamente",
    # Reportes
    "reporte.generar": "Generar reportes: activar la creación automática de estadísticas, gráficos y análisis post-simulación",
    "reporte.steps": "Intervalo de reporte: cada cuántos steps de simulación recopilar métricas. 60 = cada minuto de simulación virtual",
    "reporte.tiempo_total_espera_maximo": "Tiempo máximo total: límite de espera acumulada en segundos para considerar congestión crítica (600s = 10 min)",
    "reporte.tiempo_zona_espera_maximo": "Tiempo máximo por zona: límite de espera por zona individual para detectar cuellos de botella (300s = 5 min)",
    "reporte.total_vehiculos_maximo": "Umbral de vehículos totales: número mínimo de vehículos en el sistema para considerar que hay tráfico significativo",
    "reporte.zona_vehiculos_maximo": "Umbral por zona: número máximo de vehículos por zona antes de considerar saturación crítica",
    "reporte.path_reporte": "Directorio de reportes: carpeta donde se guardan archivos CSV, gráficos PNG y análisis estadísticos post-simulación",
    "reporte.db_path_base": "Alertas de congestión: directorio donde se almacena la BD SQLite con registros de momentos críticos cuando se superaron umbrales de tráfico",
}


def get_tooltip(field_path: str) -> str | None:
    """
    Obtener tooltip para un campo específico.

    Args:
        field_path: Ruta del campo (ej: 'services.simulation_port')

    Returns:
        Tooltip correspondiente o None si no existe
    """
    return CONFIG_TOOLTIPS.get(field_path)


def get_all_tooltips() -> dict[str, str]:
    """
    Obtener todos los tooltips disponibles.

    Returns:
        Diccionario completo de tooltips
    """
    return CONFIG_TOOLTIPS.copy()


def has_tooltip(field_path: str) -> bool:
    """
    Verificar si existe tooltip para un campo.

    Args:
        field_path: Ruta del campo

    Returns:
        True si existe tooltip, False en caso contrario
    """
    return field_path in CONFIG_TOOLTIPS


def get_tooltips_by_category(category_prefix: str) -> dict[str, str]:
    """
    Obtener tooltips filtrados por categoría.

    Args:
        category_prefix: Prefijo de categoría (ej: 'decision.entrenamiento_simplificado')

    Returns:
        Diccionario de tooltips que coinciden con el prefijo
    """
    return {
        key: value
        for key, value in CONFIG_TOOLTIPS.items()
        if key.startswith(category_prefix)
    }
