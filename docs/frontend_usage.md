# Frontend de Configuración - Guía de Uso

## Descripción

El Frontend de Configuración es una interfaz web basada en Streamlit que proporciona una forma intuitiva de gestionar la configuración del Sistema de Tráfico Inteligente, controlar servicios y realizar backups.

## Características Principales

### 🔧 Editor de Configuración
- **Edición en tiempo real** con validación automática usando Pydantic
- **Interfaz intuitiva** con widgets específicos para cada tipo de dato
- **Validación inmediata** que muestra errores antes de guardar
- **Vista previa de cambios** antes de aplicar modificaciones
- **Rollback automático** en caso de errores de validación

### 🎮 Gestión de Servicios
- **Control completo** de todos los servicios del sistema
- **Monitoreo en tiempo real** de estado, CPU, memoria y tiempo de actividad
- **Inicio/parada/reinicio** de servicios individuales o todos a la vez
- **Health checks** automáticos con recomendaciones de recuperación
- **Detección de crashes** y notificaciones automáticas

### 💾 Sistema de Backups
- **Backups automáticos** antes de cada cambio de configuración
- **Gestión completa** de backups con metadatos (fecha, tamaño)
- **Restauración segura** con confirmación y validación previa
- **Vista previa** del contenido de backups antes de restaurar
- **Comparación** entre configuración actual y backups

### 📊 Monitoreo y Alertas
- **Dashboard de rendimiento** con métricas del sistema
- **Alertas automáticas** por alto uso de recursos
- **Estadísticas de uptime** de servicios
- **Log de operaciones** con historial completo
- **Gráficos en tiempo real** de uso de CPU y memoria

## Instalación y Configuración

### Requisitos Previos

- Python 3.11 o superior
- Poetry para gestión de dependencias
- Todas las dependencias del proyecto principal

### Instalación

Las dependencias del frontend ya están incluidas en el `pyproject.toml` principal:

```bash
# Instalar todas las dependencias
poetry install
```

### Verificación de Instalación

```bash
# Verificar que Streamlit esté instalado
poetry run streamlit --version

# Verificar dependencias específicas del frontend
poetry run python -c "import streamlit, psutil, pydantic; print('✅ Dependencias OK')"
```

## Uso

### Inicio Básico

```bash
# Iniciar el frontend (método recomendado)
poetry run streamlit run run_frontend.py
```

### Opciones Avanzadas

```bash
# Puerto personalizado
poetry run streamlit run run_frontend.py --server.port 8502

# Modo debug
poetry run streamlit run run_frontend.py --logger.level debug

# Sin abrir navegador automáticamente
poetry run streamlit run run_frontend.py --server.headless true

# Mostrar ayuda
poetry run python run_frontend.py --help
```

### Acceso Web

Una vez iniciado, el frontend estará disponible en:
- **URL Local**: http://localhost:8501
- **URL de Red**: http://[tu-ip]:8501

## Estructura de la Interfaz

### 📋 Página Principal (Dashboard)
- Resumen del estado del sistema
- Métricas principales de servicios
- Alertas y notificaciones importantes

### ⚙️ Editor de Configuración
- **Secciones organizadas**: Services, Detección, Decisión, SUMO, Reporte
- **Validación en tiempo real**: Errores mostrados inmediatamente
- **Widgets inteligentes**: Específicos para cada tipo de dato
- **Botones de acción**: Guardar, Cancelar, Restaurar

### 🎮 Control de Servicios
- **Vista de servicios**: Estado, PID, tiempo de actividad, recursos
- **Controles individuales**: Iniciar, Detener, Reiniciar
- **Controles globales**: Iniciar/Detener todos los servicios
- **Health checks**: Diagnósticos automáticos con sugerencias

### 💾 Gestión de Backups
- **Lista de backups**: Con fecha, hora y tamaño
- **Crear backup**: Manual o automático antes de cambios
- **Restaurar**: Con confirmación y vista previa
- **Comparar**: Diferencias entre configuraciones

## Funcionalidades Avanzadas

### Validación de Configuración

El frontend utiliza los mismos modelos Pydantic que el sistema principal:

```python
# Validación automática al editar
- Tipos de datos correctos
- Rangos de valores válidos
- Dependencias entre campos
- Formato de archivos y rutas
```

### Manejo de Errores

- **Rollback automático**: Si la validación falla después de guardar
- **Backups de seguridad**: Creados antes de cada cambio
- **Mensajes detallados**: Con sugerencias de corrección
- **Log de errores**: Para debugging y auditoría

### Monitoreo de Servicios

```python
# Métricas monitoreadas
- Estado del proceso (PID, tiempo de actividad)
- Uso de CPU y memoria
- Puertos en uso
- Health checks automáticos
- Detección de crashes
```

## Solución de Problemas

### Problemas Comunes

#### Frontend no inicia
```bash
# Verificar dependencias
poetry install

# Verificar Python
python --version  # Debe ser 3.11+

# Verificar Poetry
poetry --version
```

#### Error de puerto ocupado
```bash
# Usar puerto diferente
poetry run streamlit run run_frontend.py --server.port 8502

# O encontrar qué proceso usa el puerto
netstat -tulpn | grep 8501  # Linux
netstat -ano | findstr 8501  # Windows
```

#### Problemas de configuración
- El frontend creará una configuración por defecto si no existe `config.yaml`
- Usa la página de Backups para restaurar una configuración válida
- Revisa los logs en la consola para errores específicos

#### Servicios no responden
- Verifica que Poetry esté disponible: `poetry --version`
- Asegúrate de que no hay conflictos de puertos
- Revisa los logs de servicios en la interfaz
- Usa los health checks para diagnósticos automáticos

### Logs y Debugging

```bash
# Logs del frontend
tail -f logs/frontend.log

# Modo debug
poetry run streamlit run run_frontend.py --logger.level debug

# Variables de entorno útiles
export STREAMLIT_LOGGER_LEVEL=DEBUG
export STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=true
```

## Integración con el Sistema Principal

### Archivos de Configuración

El frontend trabaja directamente con:
- **`config.yaml`**: Configuración principal del sistema
- **`src/traffic_system/core/config_models.py`**: Modelos de validación
- **Scripts de servicios**: `run_*_provider.py`

### Flujo de Trabajo Recomendado

1. **Configuración**: Usar el frontend para editar `config.yaml`
2. **Validación**: El frontend valida automáticamente los cambios
3. **Backup**: Se crea backup automático antes de guardar
4. **Servicios**: Controlar servicios desde la interfaz
5. **Monitoreo**: Supervisar el estado del sistema en tiempo real

### Compatibilidad

- **Configuración**: 100% compatible con el sistema principal
- **Servicios**: Usa los mismos comandos Poetry que el sistema
- **Validación**: Mismos modelos Pydantic que el core
- **Logs**: Integrado con el sistema de logging principal

## Desarrollo y Extensión

### Estructura del Código

```
src/traffic_system/frontend/
├── app.py                          # Aplicación principal Streamlit
├── components/
│   ├── config_editor.py           # Editor de configuración
│   └── service_dashboard.py       # Dashboard de servicios
└── utils/
    ├── config_handler.py          # Manejo de configuración
    ├── service_manager.py          # Gestión de servicios
    ├── service_error_handler.py   # Manejo de errores
    └── validators.py               # Validadores personalizados
```

### Agregar Nuevas Funcionalidades

1. **Nuevos componentes**: Crear en `components/`
2. **Utilidades**: Agregar en `utils/`
3. **Validadores**: Extender `validators.py`
4. **Páginas**: Agregar en `app.py`

### Testing

```bash
# Tests del frontend (cuando estén disponibles)
poetry run pytest tests/frontend/

# Test manual
poetry run streamlit run run_frontend.py
```

## Seguridad

### Consideraciones de Seguridad

- **Acceso local**: Por defecto solo accesible desde localhost
- **Validación**: Toda entrada es validada antes de procesarse
- **Backups**: Automáticos antes de cambios críticos
- **Logs**: Auditoría completa de todas las operaciones

### Configuración de Red

```bash
# Solo localhost (por defecto)
poetry run streamlit run run_frontend.py

# Acceso desde la red (usar con precaución)
poetry run streamlit run run_frontend.py --server.address 0.0.0.0
```

## Contribución

Para contribuir al desarrollo del frontend:

1. Seguir las convenciones de código del proyecto
2. Usar type hints en todas las funciones
3. Documentar nuevas funcionalidades
4. Probar cambios antes de commit
5. Seguir el patrón de componentes existente

## Soporte

Para problemas específicos del frontend:

1. Revisar esta documentación
2. Verificar logs en `logs/frontend.log`
3. Usar modo debug para más información
4. Reportar issues con logs completos
