"""
Tipos comunes utilizados en todo el sistema de tráfico inteligente.

Este módulo define tipos personalizados que se utilizan consistentemente
a través de todos los componentes del sistema.
"""

from typing import TypeAlias

# Tipo para representar resoluciones de video/pantalla como (ancho, alto)
Resolution: TypeAlias = tuple[int, int]
