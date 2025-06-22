from src.traffic_system.core.config_loader import AppSettings, load_app_settings


class Application:

    # Cargas la configuración una vez al inicio
    settings: AppSettings = load_app_settings()

    # Y ahora accedes a todo con autocompletado y seguridad de tipos
    if settings.deteccion.detectar:
        print(f"Usando el modelo YOLO: {settings.deteccion.modelo}")

        if settings.deteccion.un_video.procesar:
            print(f"Procesando video: {settings.deteccion.un_video.path_origen}")

    if settings.decision.entrenamiento.entrenar:
        print(f"Entrenando por {settings.decision.entrenamiento.num_epocas} épocas.")
