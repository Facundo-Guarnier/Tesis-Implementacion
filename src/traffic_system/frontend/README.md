# Frontend de Configuración - Sistema de Tráfico

Frontend web basado en Streamlit para gestionar la configuración del sistema de semáforos inteligentes y controlar los microservicios.

## 🚀 Inicio Rápido

### Instalación de Dependencias

```bash
# Instalar Streamlit (ya incluido en pyproject.toml)
poetry install
```

### Ejecutar el Frontend

```bash
# Opción 1: Usando el script de entrada
poetry run python run_frontend.py

# Opción 2: Directamente con Streamlit
poetry run streamlit run run_frontend.py

# Opción 3: Usando el módulo
poetry run streamlit run src/traffic_system/frontend/app.py
```

El frontend estará disponible en: **http://localhost:8501**

### Pruebas Básicas

```bash
# Ejecutar tests básicos de componentes
poetry run python test_frontend_basic.py
```

## 📱 Funcionalidades

### 🏠 Dashboard
- Vista general del estado del sistema
- Métricas de servicios y recursos
- Acciones rápidas (iniciar/detener todos los servicios)
- Backup rápido de configuración

### ⚙️ Configuración
- Editor visual para todas las secciones del `config.yaml`
- Validación en tiempo real usando modelos Pydantic
- Organización por secciones colapsables:
  - 🌐 Configuración Base (URLs, IPs)
  - 🔌 Servicios (puertos)
  - 👁️ Detección (YOLOv8, videos, cámara)
  - 🧠 Decisión/DQN (entrenamiento, hiperparámetros)
  - 🚗 Simulación SUMO (GUI, semillas, comparación)
  - 📊 Reportes (umbrales, paths)

### 🔧 Servicios
- Control de microservicios individuales
- Estado en tiempo real (PID, CPU, memoria, runtime)
- Botones de control: Iniciar ▶️, Detener ⏹️, Reiniciar 🔄
- Detección automática de dependencias
- Monitoreo de puertos y conflictos

### 📦 Backups
- Creación de backups timestamped automáticos
- Lista de backups disponibles con metadata
- Restauración segura con backup pre-restauración
- Limpieza automática de backups antiguos

### ℹ️ Información
- Información del sistema y versiones
- Documentación de servicios
- Métricas de recursos del sistema

## 🏗️ Arquitectura

### Estructura de Archivos

```
src/traffic_system/frontend/
├── app.py                    # Aplicación principal Streamlit
├── components/               # Componentes de UI (futuro)
├── utils/
│   ├── config_handler.py    # Manejo de archivos YAML
│   ├── service_manager.py   # Control de procesos/servicios
│   └── validators.py        # Validación con Pydantic
└── README.md                # Esta documentación
```

### Componentes Principales

#### ConfigHandler
- Lectura/escritura atómica de `config.yaml`
- Sistema de backups con timestamps
- Validación básica de estructura
- Operaciones seguras con archivos temporales

#### ServiceManager
- Detección de procesos por nombre de script
- Control de servicios usando `poetry run`
- Monitoreo de recursos (CPU, memoria)
- Gestión de dependencias entre servicios
- Health checks automáticos

#### ConfigValidator
- Integración con modelos Pydantic existentes
- Validación en tiempo real de campos
- Formateo de errores para UI
- Constraints y tipos de datos

## 🔧 Configuración

### Variables de Entorno

El frontend usa la configuración existente del proyecto:

- **Config Path**: `config.yaml` (raíz del proyecto)
- **Backup Directory**: `backups/config/`
- **Log Level**: INFO (configurable)

### Puertos y Servicios

Los servicios gestionados son:

| Servicio | Script | Puerto | Descripción |
|----------|--------|--------|-------------|
| simulation | `run_simulation_provider.py` | 5000 | Simulación SUMO |
| decision | `run_decision_agent.py` | - | Agente DQN |
| detection | `run_detection_provider.py` | 5000* | Detección YOLOv8 |
| reporting | `run_reporting_service.py` | 5001 | Reportes |

*Nota: detection comparte puerto con simulation*

## 🛠️ Desarrollo

### Agregar Nuevas Secciones de Configuración

1. **Actualizar `render_config_page()`** en `app.py`:
```python
config_sections = {
    "🆕 Nueva Sección": ["nueva_seccion"],
    # ... otras secciones
}
```

2. **Agregar validación** en `validators.py`:
```python
field_constraints = {
    'nueva_seccion.campo': {
        'type': 'string',
        'description': 'Descripción del campo'
    }
}
```

### Agregar Nuevos Servicios

1. **Actualizar `SERVICES`** en `service_manager.py`:
```python
SERVICES = {
    'nuevo_servicio': {
        'command': ['poetry', 'run', 'python', 'run_nuevo_servicio.py'],
        'script': 'run_nuevo_servicio.py',
        'port': 5002,
        'description': 'Descripción del servicio'
    }
}
```

### Personalizar Widgets

Los widgets se generan automáticamente según el tipo de dato:

- `bool` → `st.checkbox()`
- `int/float` → `st.number_input()`
- `str` → `st.text_input()`
- `list` → `st.text_area()` (líneas separadas)
- `dict` → Sección expandible recursiva

## 🐛 Troubleshooting

### Problemas Comunes

#### "Error cargando configuración"
- Verificar que `config.yaml` existe en la raíz del proyecto
- Comprobar sintaxis YAML válida
- Revisar permisos de lectura del archivo

#### "Servicio no se puede iniciar"
- Verificar que Poetry está instalado y en PATH
- Comprobar que no hay conflictos de puertos
- Revisar dependencias del servicio

#### "Validación falla"
- Verificar que los modelos Pydantic están actualizados
- Comprobar tipos de datos en la configuración
- Revisar campos requeridos faltantes

### Logs y Debugging

```bash
# Ver logs del frontend
poetry run streamlit run run_frontend.py --logger.level debug

# Logs de servicios gestionados
# Los logs aparecen en la consola donde se ejecuta cada servicio
```

### Limpiar Cache

Si hay problemas con el estado de la aplicación:

1. Cerrar el frontend (Ctrl+C)
2. Limpiar cache de Streamlit: `streamlit cache clear`
3. Reiniciar: `poetry run streamlit run run_frontend.py`

## 📚 Referencias

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Documentación del Proyecto Principal](../../../README.md)
