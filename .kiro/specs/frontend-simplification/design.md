# Design Document

## Overview

El diseño propone una simplificación radical del frontend actual, reduciendo de ~2500 líneas de código complejo a menos de 500 líneas distribuidas en 4 archivos principales. La solución elimina toda la sobre-ingeniería manteniendo únicamente las dos funcionalidades esenciales: gestión de configuración y control de servicios.

### Principios de Diseño

1. **Simplicidad sobre funcionalidad**: Solo implementar lo estrictamente necesario
2. **Código mínimo**: Evitar abstracciones innecesarias y patrones complejos
3. **Funcionalidad directa**: Interacción directa con archivos y procesos sin capas intermedias
4. **Mantenibilidad**: Código claro y directo que cualquier desarrollador pueda entender
5. **Logging estratégico**: Solo errores y advertencias importantes, sin logs excesivos

## Architecture

### Arquitectura Simplificada

```
Frontend Simplificado
├── app.py (150-200 líneas)          # Aplicación principal Streamlit
├── config_manager.py (100-150 líneas) # Gestión directa de config.yaml
├── service_controller.py (100-150 líneas) # Control directo de procesos
└── utils.py (50-100 líneas)         # Utilidades básicas y logging
```

### Eliminaciones Importantes

**Componentes a eliminar completamente:**
- `components/config_editor.py` (editor complejo con múltiples archivos)
- `components/service_dashboard.py` (dashboard innecesario)
- `utils/validation_utils.py` (validaciones complejas redundantes)
- `utils/validators.py` (validadores duplicados)
- `utils/service_error_handler.py` (manejo complejo de errores)
- Sistema de logs de auditoría complejo
- Métricas y dashboards avanzados
- Auto-refresh complejo con múltiples timers
- Health checks avanzados y troubleshooting

**Componentes a mantener/simplificar:**
- **Validación Pydantic**: Mantener usando AppSettings existente
- **Comentarios del config.yaml**: Usar como ayuda contextual
- **Logging básico**: Solo errores y advertencias importantes
- **Manejo de errores**: Simplificado pero preciso

## Components and Interfaces

### 1. Aplicación Principal (app.py)

**Responsabilidades:**
- Navegación simple entre 2 páginas
- Renderizado de páginas de configuración y servicios
- Manejo básico de estado de sesión

**Interfaz:**
```python
def main() -> None:
    """Función principal de la aplicación"""

def render_navigation() -> str:
    """Navegación simple con 2 botones"""

def render_config_page() -> None:
    """Página de configuración con formularios básicos"""

def render_services_page() -> None:
    """Página de servicios con botones de control"""
```

### 2. Gestor de Configuración (config_manager.py)

**Responsabilidades:**
- Lectura directa de config.yaml con comentarios preservados
- Escritura directa de config.yaml manteniendo formato
- Validación precisa usando Pydantic AppSettings
- Extracción de comentarios para ayuda contextual

**Interfaz:**
```python
class ConfigManager:
    def load_config(self) -> dict:
        """Cargar configuración desde config.yaml"""

    def save_config(self, config: dict) -> tuple[bool, list[str]]:
        """Guardar configuración a config.yaml con validación Pydantic"""

    def validate_with_pydantic(self, config: dict) -> tuple[bool, list[str]]:
        """Validación completa usando AppSettings de Pydantic"""

    def get_field_help(self, field_path: str) -> str:
        """Obtener comentario de ayuda para un campo específico"""

    def get_field_constraints(self, field_path: str) -> dict:
        """Obtener restricciones de validación para un campo"""

    def validate_basic_types(self, config: dict) -> tuple[bool, list[str]]:
        """Validación básica de tipos de datos"""
```

### 3. Controlador de Servicios (service_controller.py)

**Responsabilidades:**
- Ejecutar archivos run_*.py usando subprocess
- Verificar estado de procesos usando psutil
- Terminar procesos de servicios

**Interfaz:**
```python
class ServiceController:
    def get_service_status(self, service_name: str) -> bool:
        """Verificar si un servicio está ejecutándose"""

    def start_service(self, service_name: str) -> tuple[bool, str]:
        """Iniciar un servicio específico"""

    def stop_service(self, service_name: str) -> tuple[bool, str]:
        """Detener un servicio específico"""

    def get_all_services_status(self) -> dict[str, bool]:
        """Estado de todos los servicios"""
```

### 4. Utilidades (utils.py)

**Responsabilidades:**
- Logging básico con emojis
- Funciones auxiliares simples

**Interfaz:**
```python
def setup_logging() -> logging.Logger:
    """Configurar logging básico"""

def log_error(message: str) -> None:
    """Log de errores con emoji ❌"""

def log_warning(message: str) -> None:
    """Log de advertencias con emoji ⚠️"""

def log_success(message: str) -> None:
    """Log de éxito con emoji ✅"""
```

## Data Models

### Configuración con Validación Precisa

**Estructura de datos:**
- Usar el modelo Pydantic existente (AppSettings) para validación
- Mantener diccionarios Python para manipulación en UI
- Validación completa con restricciones específicas
- Comentarios del config.yaml como ayuda contextual

**Validación usando modelo existente:**
```python
from src.traffic_system.core.config_models import AppSettings

def validate_config(config_dict: dict) -> tuple[bool, list[str]]:
    """Validar usando el modelo Pydantic completo"""
    try:
        AppSettings(**config_dict)
        return True, []
    except ValidationError as e:
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        return False, errors
```

**Comentarios como ayuda:**
```python
FIELD_HELP = {
    'services.simulation_port': 'Puerto para el servicio de simulación SUMO',
    'deteccion.detectar': 'Activar/desactivar detección de objetos con YOLO',
    'deteccion.modelo': 'Archivo del modelo YOLO (ej: yolov8n.pt)',
    'decision.steps': 'Pasos de simulación por acción del agente (reduce frecuencia)',
    'sumo.gui': 'Mostrar interfaz gráfica de SUMO (desactivar en servidores)',
    'entrenamiento.num_epocas': 'Número total de épocas de entrenamiento',
    'entrenamiento.batch_size': 'Tamaño de lote (potencia de 2, balance memoria/convergencia)'
}
```

### Estado de Servicios

**Servicios a controlar:**
```python
SERVICES = {
    'simulation': 'run_simulation_provider.py',
    'decision': 'run_decision_agent.py',
    'detection': 'run_detection_provider.py',
    'reporting': 'run_reporting_service.py'
}
```

## Error Handling

### Estrategia con Validación Precisa

1. **Validación Pydantic**: Usar AppSettings para validación completa
2. **Mensajes específicos**: Mostrar errores de validación detallados
3. **Logging estratégico**: Solo errores y advertencias importantes
4. **Recuperación inteligente**: Mantener valores válidos, rechazar inválidos

**Ejemplo de manejo de errores con Pydantic:**
```python
try:
    # Cargar configuración
    config = yaml.safe_load(file)

    # Validar con Pydantic
    validated_config = AppSettings(**config)
    return config, []

except ValidationError as e:
    # Errores específicos de validación
    errors = []
    for error in e.errors():
        field = '.'.join(str(loc) for loc in error['loc'])
        message = error['msg']
        errors.append(f"❌ {field}: {message}")
        log_warning(f"Validation error in {field}: {message}")

    return config, errors

except yaml.YAMLError as e:
    log_error(f"Error leyendo config.yaml: {e}")
    st.error(f"❌ Error en formato YAML: {e}")
    return {}, [f"Error de formato: {e}"]

except Exception as e:
    log_error(f"Error inesperado: {e}")
    st.error(f"❌ Error inesperado: {e}")
    return {}, [f"Error inesperado: {e}"]
```

**Validación en tiempo real:**
```python
def validate_field_change(field_path: str, new_value: any, current_config: dict):
    """Validar cambio de campo individual"""
    try:
        # Crear configuración temporal con el nuevo valor
        temp_config = current_config.copy()
        set_nested_value(temp_config, field_path, new_value)

        # Validar con Pydantic
        AppSettings(**temp_config)
        return True, "✅ Valor válido"

    except ValidationError as e:
        # Encontrar error específico para este campo
        for error in e.errors():
            if field_path in str(error['loc']):
                return False, f"❌ {error['msg']}"
        return False, "❌ Error de validación"
```

## Testing Strategy

### Enfoque Minimalista

**No implementar:**
- Tests unitarios complejos
- Tests de integración avanzados
- Mocks y fixtures elaborados

**Implementar únicamente:**
- Verificación manual de funcionalidades básicas
- Tests de carga/guardado de configuración
- Verificación de inicio/parada de servicios

**Criterios de testing:**
1. ¿Se puede cargar config.yaml?
2. ¿Se pueden modificar valores?
3. ¿Se puede guardar config.yaml?
4. ¿Se pueden iniciar servicios?
5. ¿Se pueden detener servicios?

## Implementation Details

### Página de Configuración

**Diseño de interfaz con validación:**
```
⚙️ Configuración del Sistema
[Recargar] [Guardar] [Cancelar]

📡 Servicios
├── Puerto Simulación: [5000] ✅ (Puerto para el servicio de simulación SUMO)
├── Puerto Detección: [5000] ✅ (Puerto para el servicio de detección YOLO)
└── Puerto Reportes: [5001] ✅ (Puerto para el servicio de reportes)

🔍 Detección
├── Activar Detección: [✓] ✅ (Iniciar la detección de objetos)
├── Modelo YOLO: [yolov8n.pt] ✅ (Modelo de detección de objetos)
├── Rotación Forzada: [0°] ✅ (0, 90, 180, 270 grados)
└── Guardar Resultados: [results/detection_results/] ✅

🧠 Decisión
├── Activar Decisión: [✓] ✅ (Iniciar la toma de decisiones)
├── Modelo Entrenado: [assets/dqn_models/...] ✅
├── Pasos por Acción: [10] ✅ (Pasos de simulación por acción del agente)
└── Ponderaciones Zonas: [1.0, 1.0, ...] ✅ (12 valores para zonas A-L)

🚦 SUMO
├── Activar Simulación: [✓] ✅ (Iniciar simulación de tráfico con SUMO)
├── Mostrar GUI: [✓] ✅ (Mostrar interfaz gráfica - desactivar en servidores)
├── Modo Comparación: [✗] ✅ (Contrastar control RL vs detección YOLO)
├── Tiempo Límite: [19500] ✅ (Límite temporal en segundos ≈ 5.4 horas)
└── Semilla Aleatoria: [✓] ✅ (Usar semilla aleatoria basada en tiempo)

📊 Reportes
├── Generar Reportes: [✓] ✅ (Generar reportes automáticos post-simulación)
├── Pasos entre Reportes: [60] ✅ (Número de pasos a considerar)
├── Tiempo Espera Máximo: [600] ✅ (Tiempo de espera máximo total en segundos)
└── Carpeta Reportes: [results/reportes] ✅

🧠 Entrenamiento (Expandible)
├── Activar Entrenamiento: [✗] ✅ (Iniciar proceso de entrenamiento del agente DQN)
├── Número de Épocas: [35] ✅ (Número total de épocas de entrenamiento)
├── Tamaño de Lote: [256] ✅ (Potencia de 2, balance memoria/convergencia)
├── Learning Rate: [0.0005] ✅ (Tasa más conservadora para evitar gradient vanishing)
└── [Ver más configuraciones avanzadas...] (Expandir para mostrar todas las opciones)
```

**Indicadores de validación:**
- ✅ Campo válido con ayuda contextual
- ❌ Campo inválido con mensaje de error específico
- ⚠️ Campo válido pero con advertencia

### Página de Servicios

**Diseño de interfaz:**
```
🔧 Control de Servicios

🟢 Simulation Provider    [Detener]
🔴 Decision Agent         [Iniciar]
🔴 Detection Provider     [Iniciar]
🟢 Reporting Service      [Detener]

[Iniciar Todos] [Detener Todos]

Estado: 2/4 servicios activos
```

### Flujo de Datos

**Configuración:**
```
config.yaml → ConfigManager.load_config() → Streamlit widgets →
ConfigManager.save_config() → config.yaml
```

**Servicios:**
```
ServiceController.get_status() → Streamlit display →
User action → ServiceController.start/stop() → subprocess/psutil
```

## Performance Considerations

### Optimizaciones Simples

1. **Cache mínimo**: Solo cachear estado de servicios por 5 segundos
2. **Polling básico**: Verificar servicios cada 30 segundos
3. **Sin auto-refresh**: Usuario debe refrescar manualmente
4. **Carga lazy**: Cargar configuración solo cuando se necesita

### Métricas de Rendimiento Esperadas

- **Tiempo de carga**: < 2 segundos
- **Tiempo de guardado**: < 1 segundo
- **Tiempo de inicio de servicio**: < 5 segundos
- **Uso de memoria**: < 50MB
- **Líneas de código total**: < 500 líneas

## Security Considerations

### Medidas Básicas

1. **Validación de entrada**: Solo tipos básicos, sin inyección
2. **Rutas seguras**: Solo acceso a config.yaml y archivos run_*.py
3. **Procesos controlados**: Solo ejecutar archivos conocidos
4. **Sin exposición de datos**: No mostrar información sensible

### Limitaciones Aceptadas

- Sin autenticación (aplicación local)
- Sin cifrado (configuración en texto plano)
- Sin auditoría avanzada (solo logs básicos)
- Sin validación de permisos (confianza en el usuario)

## Migration Strategy

### Plan de Migración

1. **Backup**: Respaldar frontend actual
2. **Reemplazo completo**: Eliminar todos los archivos existentes
3. **Implementación nueva**: Crear los 4 archivos desde cero
4. **Testing básico**: Verificar funcionalidades esenciales
5. **Deployment**: Reemplazar frontend en producción

### Datos a Preservar

- **config.yaml**: Mantener configuración actual
- **Archivos run_*.py**: No modificar (solo ejecutar)
- **Estructura de servicios**: Mantener nombres y puertos

### Rollback Plan

- Mantener backup del frontend actual
- Script simple para restaurar versión anterior
- Documentación de diferencias para troubleshooting
