"""
Configuración para el frontend del sistema de semáforos inteligentes.

Este módulo contiene archivos de configuración externos que mejoran
la mantenibilidad del código.
"""

from .tooltips import (
    get_all_tooltips,
    get_tooltip,
    get_tooltips_by_category,
    has_tooltip,
)

__all__ = [
    "get_tooltip",
    "get_all_tooltips",
    "has_tooltip",
    "get_tooltips_by_category",
]
