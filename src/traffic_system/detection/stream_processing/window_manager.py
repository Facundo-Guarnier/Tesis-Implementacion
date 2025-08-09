import logging

import cv2
import numpy as np


class WindowManager:
    """Gestiona ventanas de OpenCV para visualización de streams"""

    def __init__(self, window_name: str):
        self.window_name = window_name
        self.window_active = False
        self.should_close = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    def create_window(self, display_size: tuple[int, int] | None = None) -> bool:
        """
        Crear y configurar la ventana de visualización

        Args:
            display_size: Tamaño de ventana (ancho, alto). Si None, usa 460x820

        Returns:
            bool: True si la ventana se creó exitosamente
        """
        try:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

            # Configurar tamaño de ventana
            if display_size:
                cv2.resizeWindow(self.window_name, display_size[0], display_size[1])
            else:
                cv2.resizeWindow(self.window_name, 460, 820)

            self.window_active = True
            self.should_close = False
            self.logger.info(f"🪟 Ventana '{self.window_name}' creada")
            return True

        except cv2.error as e:
            self.logger.error(f"❌ Error creando ventana: {e}")
            return False

    def show_frame(self, frame: np.ndarray) -> bool:
        """
        Mostrar frame en la ventana

        Args:
            frame: Frame a mostrar

        Returns:
            bool: False si se debe cerrar la ventana
        """
        if not self.window_active or self.should_close:
            return False

        try:
            cv2.imshow(self.window_name, frame)

            # Verificar si la ventana fue cerrada manualmente
            if self._check_window_closed():
                return False

            return True

        except cv2.error:
            self.logger.warning("⚠️ Error mostrando frame, ventana cerrada")
            self.should_close = True
            self.window_active = False
            return False

    def _check_window_closed(self) -> bool:
        """
        Verificar si la ventana fue cerrada manualmente

        Returns:
            bool: True si la ventana fue cerrada
        """
        try:
            window_visible = cv2.getWindowProperty(
                self.window_name, cv2.WND_PROP_VISIBLE
            )
            window_aspect = cv2.getWindowProperty(
                self.window_name, cv2.WND_PROP_ASPECT_RATIO
            )

            if (
                window_visible < 1
                or window_aspect < 0
                or cv2.getWindowProperty(self.window_name, cv2.WND_PROP_AUTOSIZE) < 0
            ):
                self.logger.info("🪟 Ventana cerrada manualmente por el usuario")
                self.should_close = True
                self.window_active = False
                return True

        except cv2.error:
            self.logger.info(
                "🪟 Ventana cerrada manualmente (error accediendo propiedades)"
            )
            self.should_close = True
            self.window_active = False
            return True

        return False

    def check_keyboard_input(self) -> str | None:
        """
        Verificar entrada de teclado

        Returns:
            str | None: Tecla presionada o None
        """
        key = cv2.waitKey(1) & 0xFF
        if key != 255:  # 255 significa que no se presionó ninguna tecla
            return chr(key) if key < 128 else None
        return None

    def cleanup(self) -> None:
        """Limpiar recursos de la ventana"""
        if self.window_active:
            try:
                cv2.destroyWindow(self.window_name)
                self.logger.info(f"🪟 Ventana '{self.window_name}' cerrada")
            except cv2.error:
                # La ventana ya podría estar cerrada
                pass

        self.window_active = False
        self.should_close = True

    @property
    def is_active(self) -> bool:
        """Verificar si la ventana está activa"""
        return self.window_active and not self.should_close
