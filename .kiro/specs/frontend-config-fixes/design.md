# Design Document

## Overview

Este diseño aborda los bugs críticos del frontend de configuración mediante correcciones específicas en el manejo de estado, encoding, carga de archivos y logging. El enfoque es quirúrgico: corregir los problemas sin cambiar la arquitectura general.

## Architecture

### Problemas Identificados y Soluciones

#### 1. Reactividad del Formulario
**Problema:** Los cambios en campos no se reflejan inmediatamente ni habilitan el botón guardar.
**Causa:** Streamlit no detecta cambios en session_state correctamente.
**Solución:** Usar callbacks y keys únicos para cada widget.

#### 2. Error de Encoding
**Problema:** `'charmap' codec can't encode character '\U0001f527'` al guardar.
**Causa:** Windows usa encoding 'cp1252' por defecto, no soporta emojis Unicode.
**Solución:** Forzar encoding UTF-8 al escribir archivos YAML.

#### 3. Carga de config.yaml
**Problema:** Archivo aparece como "vacío" cuando existe.
**Causa:** Ruta incorrecta o problema en load_config().
**Solución:** Verificar ruta absoluta y mejorar detección de archivos.

#### 4. Logs Duplicados
**Problema:** Cada log aparece 2-3 veces.
**Causa:** Streamlit re-ejecuta código múltiples veces, logging se inicializa repetidamente.
**Solución:** Usar session_state para controlar inicialización única.

#### 5. Validación en Tiempo Real
**Problema:** Validación no se actualiza inmediatamente.
**Causa:** Estado de validación no se actualiza con cambios de formulario.
**Solución:** Validar en cada cambio usando callbacks.

## Components and Interfaces

### ConfigManager (Modificaciones)

```python
class ConfigManager:
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """Guardar con encoding UTF-8 explícito"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False,
                         allow_unicode=True, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Error guardando: {e}")
            return False

    def load_config(self) -> Dict[str, Any]:
        """Mejorar detección de archivos existentes"""
        if not self.config_path.exists():
            self.logger.warning("Config no encontrado, creando por defecto")
            return self._create_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                if not config:  # Archivo vacío
                    self.logger.warning("Config vacío, usando por defecto")
                    return self._create_default_config()
                return config
        except Exception as e:
            self.logger.error(f"Error cargando config: {e}")
            return self._create_default_config()
```

### App Principal (Modificaciones)

```python
def initialize_session_state():
    """Inicialización única usando flags de sesión"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.config_manager = ConfigManager()
        st.session_state.service_controller = ServiceController()
        st.session_state.config_modified = False
        st.session_state.validation_errors = {}

def render_config_field(key: str, value: Any, field_type: str):
    """Renderizar campo con callback para detectar cambios"""
    widget_key = f"config_{key}"

    if field_type == "number":
        new_value = st.number_input(
            label=key,
            value=value,
            key=widget_key,
            on_change=on_config_change,
            args=(key,)
        )
    elif field_type == "boolean":
        new_value = st.checkbox(
            label=key,
            value=value,
            key=widget_key,
            on_change=on_config_change,
            args=(key,)
        )

    return new_value

def on_config_change(field_key: str):
    """Callback ejecutado cuando cambia un campo"""
    st.session_state.config_modified = True
    # Validar campo específico
    validate_field(field_key, st.session_state[f"config_{field_key}"])
```

## Data Models

### Estado de Sesión Mejorado

```python
SessionState = {
    'initialized': bool,           # Flag de inicialización única
    'config_manager': ConfigManager,
    'service_controller': ServiceController,
    'current_config': Dict[str, Any],
    'config_modified': bool,       # Flag de cambios pendientes
    'validation_errors': Dict[str, str],  # Errores por campo
    'save_in_progress': bool,      # Flag de guardado en progreso
}
```

### Configuración por Defecto

```python
DEFAULT_CONFIG = {
    'services': {
        'simulation_port': 5000,
        'detection_port': 5000,
        'reporting_port': 5001
    },
    'deteccion': {
        'enabled': True,
        'model_path': 'assets/yolo_models/yolov8n.pt'
    },
    'decision': {
        'enabled': True,
        'model_path': 'assets/dqn_models/'
    },
    'sumo': {
        'gui': False,
        'step_length': 1.0
    },
    'reporte': {
        'enabled': True,
        'output_dir': 'results/reportes'
    }
}
```

## Error Handling

### Estrategia de Manejo de Errores

1. **Encoding Errors**: Usar UTF-8 explícitamente en todas las operaciones de archivo
2. **Validation Errors**: Capturar ValidationError de Pydantic y mostrar mensajes específicos
3. **File Errors**: Crear archivos por defecto si no existen
4. **Logging Errors**: Usar session_state para evitar re-inicialización

### Logging Mejorado

```python
def setup_logging_once():
    """Configurar logging solo una vez por sesión"""
    if 'logging_configured' not in st.session_state:
        st.session_state.logging_configured = True

        # Configurar logger sin emojis para archivos
        file_handler = logging.FileHandler('frontend.log', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        # Logger para consola con emojis (solo si terminal soporta UTF-8)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(EmojiFormatter())

        logger = logging.getLogger('frontend_simple')
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
```

## Testing Strategy

### Tests de Corrección de Bugs

1. **Test de Encoding**: Verificar guardado con caracteres Unicode
2. **Test de Reactividad**: Verificar que cambios habiliten botón guardar
3. **Test de Carga**: Verificar carga correcta de config.yaml existente
4. **Test de Logs**: Verificar que no hay duplicación de mensajes
5. **Test de Validación**: Verificar validación en tiempo real

### Casos de Prueba Específicos

```python
def test_encoding_fix():
    """Verificar que se puede guardar config con emojis en logs"""
    config_manager = ConfigManager()
    test_config = {'test': 'value'}

    # Simular log con emoji
    logger.info("✅ Test message")

    # Debe guardar sin error
    assert config_manager.save_config(test_config) == True

def test_reactivity_fix():
    """Verificar que cambios habilitan botón guardar"""
    # Simular cambio en campo
    st.session_state.config_simulation_port = 5001
    on_config_change('simulation_port')

    # Debe marcar como modificado
    assert st.session_state.config_modified == True

def test_config_loading():
    """Verificar carga correcta de config existente"""
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # No debe estar vacío si archivo existe
    assert len(config) > 0
    assert 'services' in config
```

## Implementation Plan

### Fase 1: Corrección de Encoding
- Modificar save_config() para usar UTF-8 explícito
- Actualizar logging para manejar emojis correctamente
- Probar guardado con caracteres Unicode

### Fase 2: Corrección de Reactividad
- Implementar callbacks en widgets de formulario
- Agregar on_change handlers para detectar modificaciones
- Actualizar estado de botón guardar dinámicamente

### Fase 3: Corrección de Carga
- Mejorar load_config() para detectar archivos correctamente
- Implementar creación de config por defecto
- Verificar rutas absolutas vs relativas

### Fase 4: Corrección de Logs Duplicados
- Usar session_state para controlar inicialización única
- Configurar logging solo una vez por sesión
- Eliminar re-inicializaciones innecesarias

### Fase 5: Corrección de Validación
- Implementar validación por campo en tiempo real
- Actualizar estado de errores dinámicamente
- Sincronizar validación con estado de botón guardar
