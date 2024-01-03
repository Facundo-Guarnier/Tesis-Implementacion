import cv2


def reescalar_video(ruta_entrada, ruta_salida, nueva_resolucion):
    """
    - Reduce a la mitad los fps.
    - Reescala un video a una nueva resolución.
    """
    cap = cv2.VideoCapture(ruta_entrada)
    
    ancho_original = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto_original = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Cambia a 'XVID' si no tienes problemas con los codecs
    out = cv2.VideoWriter(ruta_salida, fourcc, 15, nueva_resolucion)  # 30 fps como ejemplo, ajusta según tus necesidades
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        #! Reducir a la mitad los fps
        if cap.get(cv2.CAP_PROP_POS_FRAMES) % 2 != 0:
            continue
        
        #! Reescalar el frame
        frame_reescalado = cv2.resize(frame, nueva_resolucion)
        
        #! Escribir el frame reescalado en el nuevo video
        out.write(frame_reescalado)
        
    #! Liberar recursos
    cap.release()
    out.release()


nueva_resolucion = (720, 1280) 
ruta_video_entrada = f"Pruebas/video-original.mp4"
ruta_video_salida = f"Pruebas/video-reescalado-{nueva_resolucion[0]}x{nueva_resolucion[1]}.mp4"

reescalar_video(ruta_video_entrada, ruta_video_salida, nueva_resolucion)