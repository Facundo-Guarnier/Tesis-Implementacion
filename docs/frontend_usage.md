# 🚦 Frontend de Configuración - Guía Completa

## 📋 Descripción General

El Frontend de Configuración es una **interfaz web moderna** basada en Streamlit que proporciona control completo sobre el Sistema de Semáforos Inteligentes. Diseñada para reemplazar la edición manual de archivos de configuración, ofrece una experiencia visual intuitiva con validación en tiempo real y monitoreo avanzado.

**🌐 Acceso**: http://localhost:8501 (después de iniciar con `poetry run streamlit run run_frontend.py`)

## 🗂️ Pestañas del Frontend

### 🔧 Servicios
**Control y monitoreo de microservicios del sistema**

#### Funcionalidades Principales:
- **Gestión de servicios individuales**:
  - ▶️ Iniciar servicios detenidos
  - ⏹️ Detener servicios en ejecución
  - 🔄 Reinicializar ServiceController en caso de errores

- **Monitoreo en tiempo real**:
  - 🟢 Estado actual (activo/detenido)
  - 🆔 PID del proceso cuando está activo
  - ⏱️ Tiempo de ejecución
  - 📊 Métricas de estado

#### Visualización de Logs:
- **📄 Logs en tiempo real** con auto-refresh configurable
- **🔄 Intervalos personalizables** (0.5s a 30s para logs casi en tiempo real)
- **📋 Filtros de visualización**:
  - Cantidad de líneas a mostrar (10-500)
  - Orden cronológico (recientes primero/últimos)
  - Actualización manual o automática
- **💾 Descarga de logs completos** en formato .txt
- **📁 Ruta del archivo de log** visible para debugging

#### Servicios Monitoreados:
- **Simulación** (`run_simulation_provider.py`): SUMO + API REST
- **Decisión** (`run_decision_agent.py`): Agente DQN
- **Detección** (`run_detection_provider.py`): YOLOv8 (opcional)
- **Reportes** (`run_reporting_service.py`): Métricas y comparaciones

### ⚙️ Configuración
**Editor visual avanzado del archivo config.yaml**

#### Características Avanzadas:
- **✅ Validación en tiempo real** usando modelos Pydantic
- **🎛️ Widgets inteligentes** específicos para cada tipo de dato:
  - 🔢 Campos numéricos con rangos apropiados
  - ✔️ Checkboxes para booleanos
  - 📝 Text areas para listas y strings
  - 🎚️ Sliders para valores con formato específico

#### Secciones de Configuración:
- **🌐 Configuración Global**: URLs base, IPs, configuración de red
- **📡 Servicios**: Puertos de simulación, detección y reportes
- **🔍 Detección de Objetos**:
  - Configuración de modelos YOLO
  - Procesamiento de carpetas de dataset
  - Configuración de video individual por zonas
  - Procesamiento de cámara en tiempo real
- **🧠 Decisión y Aprendizaje**:
  - **🔬 Entrenamiento Simplificado DQN**: Configuración básica optimizada
  - **⚗️ Entrenamiento Completo DQN**: Configuración avanzada con todas las optimizaciones
  - Parámetros de red neuronal, learning rates, epsilon decay
  - Configuraciones de Double DQN, Dueling DQN, Prioritized Replay
  - Early stopping, evaluación y métricas
- **🚦 SUMO Simulación**: Paths, GUI, semillas aleatorias, límites de tiempo
- **📊 Reportes**: Umbrales de alertas, paths de base de datos

#### Sistema de Validación:
- **⚠️ Errores en tiempo real** mostrados inmediatamente
- **🔄 Botones inteligentes**:
  - 💾 Guardar (solo habilitado con cambios válidos)
  - ❌ Cancelar (restaura configuración original)
  - 🔄 Recargar (desde archivo en disco)
- **📋 Tooltips explicativos** para campos complejos
- **🎯 Validación por tipo de campo** (puertos, rangos, paths, etc.)

### 🧪 API Testing
**Interface para probar endpoints REST del sistema**

#### Funcionalidades:
- **🌐 Configuración de URL base** (por defecto http://127.0.0.1:5000)
- **📡 Testing de endpoints** de los microservicios
- **📜 Historial de requests** con respuestas
- **🔍 Inspección de respuestas** JSON formateadas
- **⚡ Testing rápido** de disponibilidad de APIs

#### Endpoints Típicos:
- `/simulation/status` - Estado de la simulación SUMO
- `/simulation/metrics` - Métricas de tráfico actuales
- `/decision/status` - Estado del agente DQN
- `/detection/status` - Estado del sistema de detección

### ⚠️ Alertas de Congestión
**Visualización avanzada de la base de datos de alertas**

#### Características Principales:
- **📊 Selección de sesiones**: Lista de archivos de base de datos ordenados por fecha
- **📅 Metadatos de sesión**: Fecha de creación, última modificación, total de registros
- **🔍 Filtros avanzados**:
  - Rango de steps de simulación
  - Límite de registros a mostrar
  - Orden cronológico (ascendente/descendente)

#### Visualización de Datos:
- **📋 Tabla interactiva** con todas las alertas de congestión
- **📈 Gráficos temporales**:
  - 🕐 Evolución de tiempos de espera totales y por zona
  - 🚗 Evolución de cantidad de vehículos totales y por zona
  - 📊 Análisis visual de tendencias de congestión

#### Datos Monitoreados:
- **Step de simulación** y timestamp
- **Tiempos de espera** totales y por zona (A-L)
- **Cantidad de vehículos** totales y por zona
- **Estados de semáforos** en el momento de la alerta
- **Umbrales superados** que generaron la alerta

#### Exportación:
- **📥 Descarga en CSV** para análisis externo
- **📊 Exportación de gráficos** en formatos de imagen

### 📊 Métricas y Comparaciones
**Análisis comparativo de rendimiento del sistema**

#### Funcionalidades:
- **📈 Comparaciones de algoritmos**: DQN vs tiempo fijo
- **📊 Métricas de entrenamiento**: Pérdidas, recompensas, epsilon decay
- **🎯 Análisis de convergencia**: Evaluación de estabilidad del modelo
- **📋 Reportes estadísticos**: Estadísticas comparativas detalladas
- **🏆 Benchmarking**: Comparación de diferentes configuraciones

## 🚀 Instalación y Configuración

### Requisitos Previos

- **Python 3.11+**: Versión mínima requerida
- **Poetry**: Gestor de dependencias del proyecto
- **Navegador web moderno**: Chrome, Firefox, Edge, Safari

### Dependencias Específicas del Frontend

El frontend utiliza las siguientes tecnologías incluidas en `pyproject.toml`:

```python
streamlit          # Framework web principal
plotly             # Gráficos interactivos
pandas             # Manipulación de datos
numpy              # Computación numérica
sqlite3            # Base de datos (incluida en Python)
psutil             # Monitoreo de sistema
pydantic           # Validación de datos
```

### Instalación

```bash
# Instalar todas las dependencias (incluye frontend)
poetry install

# Verificar instalación del frontend
poetry run python -c "import streamlit, plotly, pandas; print('✅ Frontend OK')"
```

## 🎮 Comandos de Uso

### Inicio Básico

```bash
# Comando principal para iniciar el frontend
poetry run streamlit run run_frontend.py
```

El frontend estará disponible en: **http://localhost:8501**

### Opciones Avanzadas

```bash
# Puerto personalizado
poetry run streamlit run run_frontend.py --server.port 8502

# Modo debug con logs detallados
poetry run streamlit run run_frontend.py --logger.level debug

# Ejecutar sin abrir navegador automáticamente
poetry run streamlit run run_frontend.py --server.headless true

# Permitir acceso desde otras máquinas (usar con precaución)
poetry run streamlit run run_frontend.py --server.address 0.0.0.0

# Mostrar todas las opciones disponibles
poetry run streamlit run --help
```

### Verificación de Funcionamiento

```bash
# Verificar que el puerto esté libre
netstat -tulpn | grep 8501  # Linux
netstat -ano | findstr 8501  # Windows

# Verificar dependencias
poetry run streamlit --version
```

## 💼 Casos de Uso Prácticos

### 🔧 Configuración Inicial del Sistema
1. **Abrir el frontend**: `poetry run streamlit run run_frontend.py`
2. **Ir a pestaña "Configuración"**
3. **Modificar parámetros** necesarios con validación en tiempo real
4. **Guardar cambios** cuando no haya errores de validación
5. **Verificar** que los cambios se reflejen en `config.yaml`

### 🎯 Monitoreo Durante Experimentos
1. **Iniciar servicios** desde la pestaña "Servicios"
2. **Monitorear logs** en tiempo real con auto-refresh
3. **Revisar alertas** en la pestaña "Alertas" si se superan umbrales
4. **Analizar métricas** en la pestaña "Comparaciones"

### 🐛 Debugging de Problemas
1. **Verificar estado** de servicios en tiempo real
2. **Revisar logs detallados** con filtros de fecha/líneas
3. **Reinicializar ServiceController** si hay errores de métodos
4. **Probar APIs** en la pestaña "API Testing"

### 📊 Análisis de Resultados
1. **Exportar alertas** desde la base de datos en formato CSV
2. **Visualizar gráficos** de evolución temporal
3. **Comparar algoritmos** en la pestaña "Métricas"
4. **Generar reportes** estadísticos para investigación

## 🔧 Troubleshooting

### Problemas Comunes

#### Frontend no inicia
```bash
# Verificar dependencias
poetry install --sync

# Verificar Python version
poetry run python --version  # Debe ser 3.11+

# Verificar Poetry
poetry --version

# Reinstalar dependencias si es necesario
poetry install --no-cache
```

#### Error "Port already in use"
```bash
# Encontrar proceso que usa el puerto
lsof -i :8501  # Linux/macOS
netstat -ano | findstr 8501  # Windows

# Usar puerto diferente
poetry run streamlit run run_frontend.py --server.port 8502

# O terminar el proceso existente
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows
```

#### Servicios no responden en el frontend
```bash
# Verificar que Poetry esté en PATH
poetry --version

# Verificar que los scripts de servicios existen
ls run_*_provider.py

# Revisar logs del frontend en la consola
# El frontend mostrará errores específicos de ServiceController
```

#### Problemas de configuración/validación
- **El frontend creará config.yaml por defecto** si no existe
- **Usa la validación en tiempo real** para corregir errores antes de guardar
- **Revisa tooltips** para entender qué valor se espera en cada campo
- **Los errores específicos se muestran** debajo de cada campo problemático

#### Interfaz web no se ve correctamente
```bash
# Limpiar caché del navegador
# Ctrl+Shift+R (forzar recarga)

# Probar en navegador diferente
# Chrome, Firefox, Edge

# Verificar que no hay proxy/firewall bloqueando
# curl http://localhost:8501
```

### Logs y Debugging

```bash
# Ver logs del frontend en tiempo real
tail -f logs/frontend.log  # Si existe

# Modo debug completo
poetry run streamlit run run_frontend.py --logger.level debug

# Variables de entorno útiles para debugging
export STREAMLIT_LOGGER_LEVEL=DEBUG
export STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=true
export STREAMLIT_GLOBAL_DEVELOPMENT_MODE=true
```

## 🔒 Consideraciones de Seguridad

### Acceso y Permisos
- **Por defecto**: Solo accesible desde `localhost`
- **Archivos de configuración**: El frontend puede leer/escribir `config.yaml`
- **Servicios**: Puede iniciar/detener procesos via Poetry
- **Base de datos**: Solo lectura de archivos SQLite de alertas

### Configuración Segura
```bash
# Solo localhost (recomendado)
poetry run streamlit run run_frontend.py

# Red local (usar solo en entornos seguros)
poetry run streamlit run run_frontend.py --server.address 192.168.1.100

# NUNCA usar en producción sin autenticación
# --server.address 0.0.0.0
```

## 🤝 Desarrollo y Contribución

### Estructura del Código Frontend

```
src/traffic_system/frontend/
├── app.py                     # Aplicación principal Streamlit
├── config_manager.py          # Gestión de configuración
├── service_controller.py      # Control de servicios
├── config/
│   └── tooltips.py           # Tooltips para campos
└── utils/
    └── utils.py              # Utilidades comunes
```

### Agregar Nuevas Funcionalidades

1. **Nuevas pestañas**: Agregar función `render_nueva_pestaña()` en `app.py`
2. **Widgets personalizados**: Extender `render_field_widget()` en `app.py`
3. **Validaciones**: Agregar en `utils/utils.py`
4. **Tooltips**: Actualizar `config/tooltips.py`

### Convenciones de Desarrollo

```python
# Usar emojis para consistencia visual
st.title("🔧 Nueva Funcionalidad")

# Manejo de errores con logging
try:
    # código
except Exception as e:
    log_error(f"Error en nueva_funcionalidad: {e}")
    st.error(f"❌ Error: {e}")

# Session state para persistencia
if "nueva_variable" not in st.session_state:
    st.session_state.nueva_variable = valor_inicial
```

## 📚 Referencias

- **[Streamlit Documentation](https://docs.streamlit.io/)**: Framework web principal
- **[Plotly Documentation](https://plotly.com/python/)**: Gráficos interactivos
- **[Pydantic Documentation](https://docs.pydantic.dev/)**: Validación de datos
- **[Quickstart Guide](../quickstart.md)**: Configuración rápida del proyecto
- **[Project Structure](../1_setup/project_structure.md)**: Arquitectura del sistema
