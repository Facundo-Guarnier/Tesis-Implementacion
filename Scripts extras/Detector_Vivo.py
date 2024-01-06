import time
import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO


class Detector_Vivo:
    
    def __init__(self):
        self.clases = [2, 3, 5, 7]

        self.model = YOLO(r"Modelos/yolov8n.pt")
        self.CLASES  = self.model.model.names

        self.byte_tracker = sv.ByteTrack(track_thresh=0.25, track_buffer=30, match_thresh=0.8, frame_rate=30)
        
        self.box_annotator = sv.BoxAnnotator(
            thickness=max(1, int(4)), 
            text_thickness=max(1, int(3)), 
            text_scale=max(1, int(2 )),
        )
    
    
    def callback(self, frame, detections):
        results = self.model(frame, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)
        # detections = detections[np.isin(detections.class_id, self.clases)]
        detections = self.byte_tracker.update_with_detections(detections)

        etiquetas = []
        for xyxy, mask, confidence, class_id, tracker_id in detections:
            etiqueta = f"{self.CLASES[class_id]} {confidence:0.2f}"
            etiquetas.append(etiqueta)
        
        print(etiquetas)
        frame = self.box_annotator.annotate(
            frame, 
            detections=detections,
            labels=etiquetas,
        )

        return frame


    def video(self, guardar=False):
        # cap = cv2.VideoCapture(r"Pruebas\video-original.mp4")
        cap = cv2.VideoCapture(0)
        # cap = cv2.VideoCapture(r"Pruebas\video-original.mp4")  # 0 es generalmente el índice de la cámara web predeterminada
        
        if guardar:
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter('video_procesado.mp4', fourcc, fps, (width, height))

        
        start_time = time.time()
        total_t = 0
        total_frames = 0
        
        while True:
            ret, frame = cap.read()  # Leer un fotograma del video
            if not ret:
                break
            
            start_t = time.time()
            results = self.model(frame)[0]
            end_t = time.time()
            
            total_t += end_t - start_t
            total_frames += 1
            
            detections = sv.Detections.from_ultralytics(results)
            annotated_frame = self.callback(frame, detections)
            
            cv2.imshow('frame', annotated_frame)  # Mostrar el fotograma anotado
            
            if guardar:
                out.write(annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Salir del bucle si se presiona 'q'
                break

        print(f"Tiempo total: {time.time() - start_time}")
        print(f"Tiempo promedio: {total_t / total_frames}")
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    d = Detector_Vivo()
    d.video(False)
    print("Terminado")
