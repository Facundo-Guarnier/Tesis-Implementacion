# 🤝 Guía de Contribución

Para mantener la consistencia y la calidad del código, por favor sigue las siguientes guías.

## 🌱 Flujo de Trabajo con Ramas (Branching)

Usamos un modelo de ramas simple pero robusto para organizar el trabajo.

### 🌳 Ramas Principales

- `main`: Contiene la versión estable y de producción del proyecto. Solo se actualiza mediante Pull Requests desde la rama `develop`.
- `develop`: Es la rama de integración principal. Todas las nuevas funcionalidades y correcciones se fusionan aquí antes de pasar a `main`. **Todo el trabajo nuevo debe partir de esta rama.**

### 🌿 Ramas de Trabajo

Cada nueva tarea (funcionalidad, corrección, etc.) debe realizarse en su propia rama. El nombre de la rama debe seguir el formato `tipo/descripcion-corta`.

- **`feature/`**: Para nuevas funcionalidades.
  - _Ejemplo:_ `feature/deteccion-ambulancias`
- **`fix/`**: Para correcciones de errores (bugs).
  - _Ejemplo:_ `fix/error-calculo-tiempos`
- **`docs/`**: Para añadir o mejorar la documentación.
  - _Ejemplo:_ `docs/actualizar-guia-contribucion`
- **`refactor/`**: Para cambios en el código que no añaden funcionalidades ni corrigen errores (ej. mejorar rendimiento, simplificar código).
  - _Ejemplo:_ `refactor/simplificar-clase-detector`

## 📝 Estilo de Commits (Conventional Commits)

Utilizamos el estándar **Conventional Commits** para los mensajes de commit. Esto nos ayuda a mantener un historial claro y nos permite automatizar la generación del `changelog`.

La estructura de un commit es:

```
tipo(ámbito): descripción corta en imperativo
```

- **tipo**: Define la categoría del cambio (ver tabla abajo).
- **(ámbito)**: (Opcional) El módulo o parte del proyecto afectado (ej. `api`, `detector`, `docs`).
- **descripción**: Un resumen claro y conciso de lo que hace el commit.

| Tipo       | Descripción                                                                              |
| ---------- | ---------------------------------------------------------------------------------------- |
| `Feature`  | Una nueva funcionalidad (ej. `feature(api): agregar endpoint de reportes`)               |
| `Fix`      | Una corrección de un error (ej. `fix(detector): corregir conteo duplicado`)              |
| `Docs`     | Cambios exclusivos en la documentación (ej. `docs: añadir guía de vscode`)               |
| `Style`    | Cambios de formato que no afectan la lógica (ej. `style: aplicar black`)                 |
| `Refactor` | Cambios en el código que no son ni `fix` ni `feature` (ej. `refactor: optimizar bucle`)  |
| `Test`     | Añadir o corregir tests (ej. `test: crear prueba para la lógica de semáforos`)           |
| `Chore`    | Tareas de mantenimiento (ej. `chore: actualizar dependencias en pip`)                    |
| `WIP`      | Trabajo en progreso, no listo para producción (ej. `wip: empezar implementación de API`) |

## 📤 Proceso de Pull Request (PR)

1.  **Sincroniza y crea tu rama:** Asegúrate de tener la última versión de `develop` y crea tu rama de trabajo desde ahí.
    `bash
git checkout develop
git pull origin develop
git checkout -b tipo/tu-descripcion
`
2.  **Trabaja y haz commits:** Realiza tus cambios y haz commits siguiendo el estilo definido.
3.  **Sube tu rama:** `git push -u origin tipo/tu-descripcion`
4.  **Abre un Pull Request:** Ve a GitHub y abre un PR desde tu rama hacia `develop`.
5.  **Describe tu PR:** El título debe ser claro y el cuerpo debe explicar qué cambios hiciste y por qué. Si el PR resuelve una "Issue", enlázala.
6.  **Revisa y fusiona:** Una vez que el PR es aprobado (y las verificaciones automáticas pasan), se fusionará en `develop`.

## 🎨 Estilo y Calidad de Código

Antes de hacer un commit, asegúrate de que tu código cumple con las guías de estilo y calidad definidas en el proyecto. Las herramientas (`ruff`, `black`) configuradas en VS Code deberían ayudarte con esto automáticamente.

- **Guía de estilo de código:** [`./code_style.md`](./code_style.md)
- **Herramientas de calidad:** [`./tooling.md`](./tooling.md)

## 🌐 Desarrollo del Frontend

### Dependencias Específicas

El frontend utiliza tecnologías adicionales incluidas en `pyproject.toml`:

```python
streamlit          # Framework web principal
plotly             # Gráficos interactivos avanzados
pandas             # Manipulación de datos y análisis
numpy              # Computación numérica
psutil             # Monitoreo de sistema y procesos
pydantic           # Validación de configuración
```

### Estructura del Frontend

```
src/traffic_system/frontend/
├── app.py                     # Aplicación principal con 5 pestañas
├── config_manager.py          # Gestión de config.yaml
├── service_controller.py      # Control de microservicios
├── config/
│   └── tooltips.py           # Tooltips explicativos
└── utils/
    └── utils.py              # Utilidades comunes
```

### Convenciones de UI/UX

#### Emojis y Consistencia Visual
```python
# Usar emojis para identificación rápida de secciones
st.title("🔧 Control de Servicios")
st.subheader("⚙️ Configuración Avanzada")

# Estados visuales consistentes
🟢 # Servicio activo/funcionando
🔴 # Servicio detenido/error
⚠️ # Advertencia/atención requerida
✅ # Operación exitosa
❌ # Error/falló
```

#### Widgets y Validación
```python
# Widgets inteligentes según tipo de dato
def render_field_widget(field_path: str, field_name: str, value: Any):
    if isinstance(value, bool):
        st.checkbox(field_name, value=value, key=widget_key)
    elif isinstance(value, int) and "port" in field_path:
        st.number_input(field_name, min_value=1, max_value=65535)
    # ... más casos específicos
```

#### Session State y Estado Persistente
```python
# Inicializar estado de sesión correctamente
if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.current_config = {}
    # ... otros estados
```

### Testing del Frontend

#### Verificación Manual
```bash
# Iniciar frontend en modo debug
poetry run streamlit run run_frontend.py --logger.level debug

# Verificar dependencias específicas
poetry run python -c "import streamlit, plotly, pandas; print('✅ Frontend OK')"

# Verificar puertos disponibles
netstat -tulpn | grep 8501  # Linux
netstat -ano | findstr 8501  # Windows
```

#### Casos de Prueba Recomendados
1. **Validación de configuración**: Probar campos inválidos en todas las secciones
2. **Control de servicios**: Iniciar/detener servicios y verificar logs
3. **Navegación**: Cambiar entre pestañas sin perder estado
4. **Responsive**: Probar en diferentes tamaños de ventana
5. **Errores de red**: Simular servicios no disponibles

### Buenas Prácticas de Desarrollo

#### Manejo de Errores
```python
# Usar logging centralizado con emojis
from src.traffic_system.frontend.utils import log_error

try:
    # operación riesgosa
    resultado = operacion_compleja()
except Exception as e:
    log_error(f"Error en operacion_compleja: {e}")
    st.error(f"❌ Error: {e}")
    return None
```

#### Performance y Caching
```python
# Usar cache de Streamlit para operaciones costosas
@st.cache_data(ttl=60)  # Cache por 60 segundos
def get_services_summary():
    return controller.get_services_summary()

# Session state para evitar recálculos
if "services_cache" not in st.session_state:
    st.session_state.services_cache = get_services_summary()
```

#### Componentes Reutilizables
```python
# Crear funciones para widgets complejos reutilizables
def render_service_status(service_name: str, is_running: bool):
    """Renderizar estado visual consistente de servicios."""
    if is_running:
        st.success(f"🟢 {service_name}")
    else:
        st.error(f"🔴 {service_name}")
```
