"""
Sistema de overlay de información profesional para videos de detección.
"""

import cv2
import numpy as np


class InfoOverlay:
    """
    Maneja la visualización profesional de información en los videos de detección.
    Agrupa toda la información en un panel organizado en la esquina superior izquierda.
    """

    def __init__(self, scale_factor: float = 1.0):
        self.scale_factor = scale_factor
        self._setup_style()

    def _setup_style(self) -> None:
        """Configurar estilos visuales para el overlay"""
        # Configuración de fuente
        self.font = cv2.FONT_HERSHEY_DUPLEX  # Fuente más clara y profesional
        self.font_scale = max(0.6, 0.6 * self.scale_factor)
        self.font_thickness = max(1, int(2 * self.scale_factor))

        # Configuración de colores (BGR format)
        self.bg_color = (0, 0, 0, 180)  # Negro semi-transparente
        self.border_color = (255, 255, 255)  # Blanco para el borde
        self.text_color = (255, 255, 255)  # Blanco para texto principal
        self.fps_color = (0, 255, 0)  # Verde para ambos FPS
        self.detection_color = (
            0,
            165,
            255,
        )  # Naranja para detección (vehículos y tiempo)
        self.info_color = (
            255,
            255,
            255,
        )  # Blanco para información general (fuente, zona)

        # Configuración de layout
        self.padding = max(10, int(10 * self.scale_factor))
        self.line_height = max(25, int(25 * self.scale_factor))
        self.section_spacing = max(
            10, int(10 * self.scale_factor)
        )  # Espaciado real entre secciones

        # Posición del panel
        self.panel_x = self.padding
        self.panel_y = self.padding

    def _calculate_text_size(self, text: str) -> tuple[int, int]:
        """Calcular el tamaño de un texto"""
        (text_width, text_height), baseline = cv2.getTextSize(
            text, self.font, self.font_scale, self.font_thickness
        )
        return text_width, text_height + baseline

    def _draw_background_panel(
        self, frame: np.ndarray, width: int, height: int
    ) -> np.ndarray:
        """Dibujar el panel de fondo semi-transparente"""
        # Crear overlay para transparencia
        overlay = frame.copy()

        # Dibujar rectángulo de fondo
        cv2.rectangle(
            overlay,
            (self.panel_x, self.panel_y),
            (self.panel_x + width, self.panel_y + height),
            self.bg_color[:3],  # Solo RGB, sin alpha
            -1,  # Rellenar
        )

        # Dibujar borde
        cv2.rectangle(
            overlay,
            (self.panel_x, self.panel_y),
            (self.panel_x + width, self.panel_y + height),
            self.border_color,
            max(1, int(2 * self.scale_factor)),
        )

        # Aplicar transparencia
        alpha = 0.7  # 70% opacidad
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        return frame

    def _draw_text_with_shadow(
        self,
        frame: np.ndarray,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        shadow_offset: int = 2,
    ) -> None:
        """Dibujar texto con sombra para mayor legibilidad"""
        # Dibujar sombra
        cv2.putText(
            frame,
            text,
            (x + shadow_offset, y + shadow_offset),
            self.font,
            self.font_scale,
            (0, 0, 0),  # Negro para sombra
            self.font_thickness + 1,
            cv2.LINE_AA,
        )

        # Dibujar texto principal
        cv2.putText(
            frame,
            text,
            (x, y),
            self.font,
            self.font_scale,
            color,
            self.font_thickness,
            cv2.LINE_AA,
        )

    def add_info_overlay(
        self,
        frame: np.ndarray,
        fps_real: int,
        fps_original: float,
        source_type: str,
        vehicle_count: int,
        wait_time_seconds: int,
        zone_name: str = "",
    ) -> np.ndarray:
        """
        Agregar overlay de información completa al frame

        Args:
            frame: Frame del video
            fps_real: FPS reales de procesamiento
            fps_original: FPS originales del video/fuente
            source_type: Tipo de fuente ("video", "camera", etc.)
            vehicle_count: Cantidad de vehículos detectados
            wait_time_seconds: Tiempo de espera en segundos
            zone_name: Nombre de la zona (opcional)
        """
        # Preparar información sin emojis ni tildes
        info_lines = [
            ("INFORMACION DE DETECCION", self.text_color, "header"),
            # FPS - mismo color verde para ambos
            (f"FPS Procesamiento: {fps_real}", self.fps_color, "fps_real"),
            (f"FPS Fuente: {fps_original:.1f}", self.fps_color, "fps_original"),
            # Separador
            ("", self.text_color, "separator"),
            # Detección - mismo color naranja para vehículos y tiempo
            (f"Vehiculos: {vehicle_count}", self.detection_color, "vehicles"),
            (f"Tiempo Espera: {wait_time_seconds}s", self.detection_color, "wait_time"),
            # Separador
            ("", self.text_color, "separator"),
            # Información general - mismo color blanco
            (f"Tipo: {source_type.capitalize()}", self.info_color, "source"),
        ]

        # Agregar zona si se especifica
        if zone_name:
            info_lines.append((f"Zona: {zone_name}", self.info_color, "zone"))

        # Calcular dimensiones del panel
        max_width = 0
        total_height = self.padding * 2

        for text, _, line_type in info_lines:
            if line_type == "separator":
                # Los separadores solo agregan espacio
                total_height += self.section_spacing
            elif line_type == "header":
                # Para el encabezado, calcular con el factor de escala aumentado
                font_scale_header = self.font_scale * 1.2
                (text_width, text_height), baseline = cv2.getTextSize(
                    text,
                    self.font,
                    font_scale_header,
                    max(2, int(self.font_thickness * 1.5)),
                )
                header_height = text_height + baseline
                max_width = max(max_width, text_width)
                total_height += header_height + self.section_spacing
            else:
                text_width, text_height = self._calculate_text_size(text)
                max_width = max(max_width, text_width)
                total_height += self.line_height

        panel_width = max_width + (self.padding * 3)  # Más padding horizontal

        # Dibujar panel de fondo
        frame = self._draw_background_panel(frame, panel_width, total_height)

        # Dibujar información línea por línea
        current_y = self.panel_y + self.padding + self.line_height

        for text, color, line_type in info_lines:
            if line_type == "separator":
                # Agregar espacio extra para separadores
                current_y += self.section_spacing
                continue
            elif line_type == "header":
                # Texto de encabezado más grande
                font_scale_header = self.font_scale * 1.2
                cv2.putText(
                    frame,
                    text,
                    (self.panel_x + self.padding, current_y),
                    self.font,
                    font_scale_header,
                    color,
                    max(2, int(self.font_thickness * 1.5)),
                    cv2.LINE_AA,
                )
                current_y += self.line_height + self.section_spacing
            else:
                # Texto normal con sombra
                self._draw_text_with_shadow(
                    frame, text, self.panel_x + self.padding, current_y, color
                )
                current_y += self.line_height

        return frame

    def add_simple_fps_overlay(
        self,
        frame: np.ndarray,
        fps_real: int,
        fps_original: float,
        source_type: str,
    ) -> np.ndarray:
        """
        Versión simplificada del overlay solo con información de FPS
        Para usar cuando no se tiene información completa de detección
        """
        return self.add_info_overlay(
            frame=frame,
            fps_real=fps_real,
            fps_original=fps_original,
            source_type=source_type,
            vehicle_count=0,
            wait_time_seconds=0,
            zone_name="",
        )
