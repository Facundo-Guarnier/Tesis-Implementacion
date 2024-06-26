import cv2, os


def reescalar_video(ruta_entrada, ruta_salida, nueva_resolucion, factor_reduccion_fps=3):
    """
    - Reduce a un tercio los fps.
    - Reescala un video a una nueva resolución.
    """
    cap = cv2.VideoCapture(ruta_entrada)
    
    ancho_original = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto_original = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    #! Obtener la tasa de fotogramas original
    fps_original = cap.get(cv2.CAP_PROP_FPS)
    
    #! Calcular la nueva tasa de fotogramas
    fps_nuevo = fps_original / factor_reduccion_fps
    
    _, extension = os.path.splitext(ruta_entrada)
    nombre_base, _ = os.path.splitext(ruta_salida)
    
    # ruta_salida = nombre_base + f"-{nueva_resolucion[0]}x{nueva_resolucion[1]}-{round(fps_nuevo)}fps{extension}"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(ruta_salida, fourcc, fps_nuevo, nueva_resolucion)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Reducir a un tercio los fps
        if cap.get(cv2.CAP_PROP_POS_FRAMES) % factor_reduccion_fps != 0:
            continue
        
        # Reescalar el frame
        frame_reescalado = cv2.resize(frame, nueva_resolucion)
        
        # Escribir el frame reescalado en el nuevo video
        out.write(frame_reescalado)

    #! Liberar recursos
    cap.release()
    out.release()
    print(f"Video reescalado: {ruta_salida}")


def reescalar_carpeta_videos(carpeta_entrada, carpeta_salida, nueva_resolucion, factor_reduccion_fps):
    #! Crear la carpeta de salida si no existe
    carpeta_salida = f"{carpeta_salida}-{nueva_resolucion[0]}x{nueva_resolucion[1]}-{round(30/factor_reduccion_fps)}fps"
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    #! Recorrer todas las carpetas en la carpeta de entrada
    for carpeta_video in os.listdir(carpeta_entrada):
        carpeta_video_ruta = os.path.join(carpeta_entrada, carpeta_video)

        #! Verificar si es una carpeta
        if os.path.isdir(carpeta_video_ruta):
            #! Crear la carpeta de salida espejo
            carpeta_salida_ruta = os.path.join(carpeta_salida, carpeta_video)
            if not os.path.exists(carpeta_salida_ruta):
                os.makedirs(carpeta_salida_ruta)

            #! Procesar todos los archivos en la carpeta de video
            for archivo_video in os.listdir(carpeta_video_ruta):
                archivo_video_ruta_entrada = os.path.join(carpeta_video_ruta, archivo_video)
                archivo_video_ruta_salida = os.path.join(carpeta_salida_ruta, archivo_video)

                #! Verificar si es un archivo y tiene una extensión de video
                if os.path.isfile(archivo_video_ruta_entrada) and archivo_video_ruta_entrada.lower().endswith(('.mp4', '.avi', '.mkv')):
                    #! Reescalar el video
                    reescalar_video(archivo_video_ruta_entrada, archivo_video_ruta_salida, nueva_resolucion, factor_reduccion_fps)


nueva_resolucion = (576, 1024)
factor_reduccion_fps = 6    #! 30/factor = fps

# #! Reescalar todos los videos carpetas 
carpeta_entrada = "Deteccion/Dataset/Dataset_original"
carpeta_salida = "Deteccion/Dataset/Dataset_reescalado"
reescalar_carpeta_videos(carpeta_entrada, carpeta_salida, nueva_resolucion, factor_reduccion_fps)

#! Reescalar un único video
# ruta_video_entrada = f"Pruebas/video-original.mp4"
# ruta_video_salida = f"Pruebas/video-reescalado"
# reescalar_video(ruta_video_entrada, ruta_video_salida, nueva_resolucion, factor_reduccion_fps)