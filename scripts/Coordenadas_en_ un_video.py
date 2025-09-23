import cv2
import numpy as np


def detectar_y_corregir_orientacion(
    frame: np.ndarray, es_video_vertical: bool = True
) -> np.ndarray:
    """
    Detecta si un frame necesita rotación y la aplica automáticamente.

    Args:
        frame: El frame de video a verificar
        es_video_vertical: True si el video debería ser vertical (alto > ancho)

    Returns:
        Frame corregido con la orientación correcta
    """
    alto, ancho = frame.shape[:2]

    # Si esperamos un video vertical pero el frame es horizontal, rotar
    if es_video_vertical and ancho > alto:
        # Rotar 90° en sentido horario para corregir la orientación
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    # Si esperamos un video horizontal pero el frame es vertical, rotar
    elif not es_video_vertical and alto > ancho:
        # Rotar 90° en sentido antihorario para corregir la orientación
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    return frame


def convertir_coordenadas_rotadas(
    x: int, y: int, ancho_original: int, alto_original: int
) -> tuple[int, int]:
    """
    Convierte coordenadas de un frame rotado 90° horario de vuelta al frame original.

    Args:
        x, y: Coordenadas en el frame rotado
        ancho_original, alto_original: Dimensiones del frame original (antes de rotar)

    Returns:
        Tupla con coordenadas (x, y) en el frame original
    """
    # Para rotación 90° horario:
    # x_original = y_rotado
    # y_original = ancho_original - x_rotado
    x_original = y
    y_original = ancho_original - x
    return x_original, y_original


class Coordinates:
    def __init__(self, video_path: str):
        self.cap = cv2.VideoCapture(video_path)
        self.pixel_coordinates: list[list[int]] = []
        self.pixel_coordinates_originales: list[list[int]] = (
            []
        )  # Coordenadas convertidas al frame original
        self.frame_rotado = False  # Para rastrear si el frame está siendo rotado
        self.dimensiones_originales = (0, 0)  # (ancho, alto) del frame original

        # Establecer el tamaño de la ventana a la mitad del tamaño original
        cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Frame", 560, 960)

        cv2.setMouseCallback("Frame", self.print_coordinates)

        self.video()

    def print_coordinates(
        self, event: int, x: int, y: int, flags: int, params: object
    ) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            # Siempre guardar las coordenadas del frame mostrado
            self.pixel_coordinates.append([x, y])

            # Si el frame fue rotado, convertir las coordenadas de vuelta al original
            if self.frame_rotado:
                ancho_orig, alto_orig = self.dimensiones_originales
                x_orig, y_orig = convertir_coordenadas_rotadas(
                    x, y, ancho_orig, alto_orig
                )
                self.pixel_coordinates_originales.append([x_orig, y_orig])

                print(f"🔄 Coordenadas en frame mostrado (rotado): [{x}, {y}]")
            else:
                # Si no hubo rotación, las coordenadas son las mismas
                self.pixel_coordinates_originales.append([x, y])
                print(f"✅ Coordenadas capturadas: [{x}, {y}]")

    def video(self) -> None:
        # Determinar si es un video vertical basándose en el nombre del directorio o resolución esperada
        # Los videos en dataset-1080x1920-30fps deberían ser verticales
        es_video_vertical = True

        # Leer el primer frame para información de depuración
        first_frame = True

        while True:
            status, frame = self.cap.read()

            if not status:
                break

            # Verificar si necesitamos rotar antes de aplicar la corrección
            alto_original, ancho_original = frame.shape[:2]
            frame_necesita_rotacion = (
                es_video_vertical and ancho_original > alto_original
            )

            # Guardar las dimensiones originales
            self.dimensiones_originales = (ancho_original, alto_original)

            # Información de depuración solo en el primer frame
            if first_frame:
                print(
                    f"🎥 Dimensiones originales del frame: {ancho_original}x{alto_original}"
                )
                print(
                    f"🔄 ¿Necesita rotación? {'Sí' if frame_necesita_rotacion else 'No'}"
                )
                if frame_necesita_rotacion:
                    print(
                        "💡 Las coordenadas se convertirán automáticamente al frame original"
                    )
                first_frame = False

            # Corregir orientación si es necesario
            frame = detectar_y_corregir_orientacion(frame, es_video_vertical)

            # Actualizar la bandera de rotación
            self.frame_rotado = frame_necesita_rotacion

            cv2.imshow("Frame", frame)

            if cv2.waitKey(70) & 0xFF == ord("q"):
                break

    def __del__(self) -> None:
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # v = "D:\\Repositorios_GitHub\\Tesis-Implementacion\\assets\\dataset-1080x1920-30fps\\Zona A\\20250829_131853.mp4"
    # v = "D:\\Repositorios_GitHub\\Tesis-Implementacion\\assets\\dataset-1080x1920-30fps\\Zona G\\20250829_131155.mp4"
    # v = "D:\\Repositorios_GitHub\\Tesis-Implementacion\\assets\\dataset-nuevos_video_2\\Zona C\\20250906_111435.mp4"
    v = "D:\\Repositorios_GitHub\\Tesis-Implementacion\\assets\\dataset-nuevos_video_3\\Zona B\\20250914_122919.mp4"
    c = Coordinates(v)

    print("\n" + "=" * 60)
    print("📋 RESUMEN DE COORDENADAS CAPTURADAS")
    print("=" * 60)
    print(f"Coordenadas en frame mostrado: {c.pixel_coordinates}")
    if c.frame_rotado:
        print(
            "\n💡 Usa 'pixel_coordinates_originales' para el frame original del video"
        )
    else:
        print(
            "✅ No se aplicó rotación - las coordenadas son directas del frame original"
        )
