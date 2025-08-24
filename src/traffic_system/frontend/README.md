# Frontend de Configuración - Sistema de Tráfico Inteligente

## Descripción

Interfaz web basada en Streamlit para la gestión completa del Sistema de Tráfico Inteligente. Proporciona una interfaz intuitiva para editar configuraciones, controlar servicios y gestionar backups.

## Inicio Rápido

```bash
# Desde el directorio raíz del proyecto
poetry run streamlit run run_frontend.py
```

Accede a http://localhost:8501 en tu navegador.

## Características

- ⚙️ **Editor de Configuración**: Edición visual de config.yaml con validación en tiempo real
- 🎮 **Control de Servicios**: Gestión completa de todos los servicios del sistema
- 💾 **Sistema de Backups**: Backups automáticos y restauración segura
- 📊 **Monitoreo**: Dashboard con métricas de rendimiento y alertas
- 🔍 **Diagnósticos**: Health checks automáticos y solución de problemas

## Estructura

```
frontend/
├── app.py                          # Aplicación principal
├── components/                     # Componentes de UI
│   ├── config_editor.py           # Editor de configuración
│   └── service_dashboard.py       # Dashboard de servicios
└── utils/                          # Utilidades
    ├── config_handler.py          # Manejo de configuración
    ├── service_manager.py          # Gestión de servicios
    ├── service_error_handler.py   # Manejo de errores
    └── validators.py               # Validadores
```

## Dependencias

- **streamlit**: Framework web
- **psutil**: Monitoreo de procesos
- **pydantic**: Validación de datos
- **pyyaml**: Manejo de YAML

## Documentación

Ver [docs/frontend_usage.md](../../../docs/frontend_usage.md) para documentación completa.

## Desarrollo

### Agregar Nuevos Componentes

1. Crear archivo en `components/`
2. Importar en `app.py`
3. Agregar a la navegación

### Validación Personalizada

Extender `validators.py` con nuevos validadores:

```python
def validate_custom_field(value: Any) -> tuple[bool, str]:
    # Lógica de validación
    return is_valid, error_message
```

### Manejo de Errores

Usar `ServiceErrorHandler` para errores consistentes:

```python
from utils.service_error_handler import ServiceErrorHandler

handler = ServiceErrorHandler()
handler.handle_service_error(error_type, service_name, details)
```

## Testing

```bash
# Test manual
poetry run streamlit run run_frontend.py

# Verificar dependencias
poetry run python -c "import streamlit, psutil, pydantic; print('OK')"
```
