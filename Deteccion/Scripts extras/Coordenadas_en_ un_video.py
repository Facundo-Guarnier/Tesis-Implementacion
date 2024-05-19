import cv2

class Coordinates:
    def __init__(self, video_path: str):
        self.cap = cv2.VideoCapture(video_path)
        self.pixel_coordinates:list[list[int]] = []

        # Establecer el tamaño de la ventana a la mitad del tamaño original
        cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Frame", 560, 960)


        cv2.setMouseCallback("Frame", self.print_coordinates)

        self.video()

    def print_coordinates(self, event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pixel_coordinates.append([x, y])

    def video(self):
        while True:
            status, frame = self.cap.read()
            
            if not status:
                break
        
            cv2.imshow("Frame", frame)

            if cv2.waitKey(70) & 0xFF == ord('q'): 
                break

    def __del__(self):
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    v = r"D:\Repositorios_GitHub\Tesis-Implementacion\Dataset\Dataset_original\Zona L\20240102_133830.mp4"
    c = Coordinates(v)
    print(c.pixel_coordinates)