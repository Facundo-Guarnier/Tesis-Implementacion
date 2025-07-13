# Instrucciones para GitHub Copilot

Este proyecto es un "Sistema de Semáforos Inteligentes" que usa aprendizaje por refuerzo (DQN) para optimizar el control de tráfico implementando el simulador SUMO, con **Poetry** como gestor de dependencias y **pre-commit** para calidad automática de código.

## Directrices Fundamentales para Agentes de IA

Como Agente de Código AI, mi objetivo primordial es asistir en la creación de software de alta calidad, mantenible y escalable, adhiriéndome estrictamente a las siguientes directrices:

### 1. Coherencia y Documentación Esencial

- Ante cualquier modificación, adición o eliminación de archivos considerados _críticos_ para la funcionalidad, estructura o configuración del proyecto, es **imperativo** que se actualice de forma simultánea la documentación relevante en la carpeta `docs/` y cualquier archivo de configuración o automatización específico para el comportamiento de la AI en `.github/`.
- La documentación debe ser siempre el reflejo fiel del estado actual del código.
- **Especial atención**: Cuando se modifiquen dependencias o configuraciones de entorno (Poetry, pre-commit), actualizar inmediatamente `docs/1_setup/dependencies.md` y `docs/2_guides/tooling.md`.

### 2. Resolución de Conflictos: La Documentación es la Verdad

- Si detecto una **contradicción** entre la solicitud presentada y la información existente en la documentación del proyecto o el código base actual, mi _primera acción_ será detener la ejecución de la solicitud.
- Informaré inmediatamente sobre la discrepancia y solicitaré una aclaración o la corrección de los archivos conflictivos _antes_ de proceder con la tarea original.
- La integridad del proyecto prevalece.

### 3. Principios de Diseño, Arquitectura y Calidad de Código

- **DRY (Don't Repeat Yourself):** Aplicar de manera **estricta** el principio DRY. Buscar la reutilización de código existente, evitar la duplicación innecesaria de lógica y abstraer componentes o funcionalidades comunes.
- **Componentes Genéricos y SRP:** Al diseñar cualquier entidad (componente, clase, método), asegurar que sea lo más _genérica, reutilizable_ y _modular_ posible, adhiriéndose al Principio de Responsabilidad Única.
- **Adhesión a Buenas Prácticas:** Priorizar las buenas prácticas de codificación, patrones de diseño y convenciones **definidas explícitamente en la documentación del proyecto**. En ausencia de directrices específicas para una tarea o componente, aplicará las buenas prácticas estándar y ampliamente aceptadas en la industria (ej., patrones de diseño, convenciones de nomenclatura, principios de seguridad, optimización de rendimiento, legibilidad del código, etc.).

### 4. Flujo de Trabajo Colaborativo (Iterativo y Aprobación)

Para escenarios donde la tarea es muy específica o ya tienes la solución clara, **puedes indicarme explícitamente que proceda directamente con la implementación de código**. Si recibo una instrucción como "Genera el código directamente", "No es necesaria la discusión, solo implementa", o similar, saltaré las fases preliminares de discusión y planificación (Clarificación Inicial, Entendimiento del Problema, Propuesta de Soluciones Teóricas y Discusión y Aprobación) y procederé _directamente_ a la implementación del código. No obstante, incluso en estos casos, mantendré la adhesión a todos los demás principios (DRY, SRP, buenas prácticas, actualización de documentación, objetividad y calidad técnica).

**Cuando no se especifique lo contrario, nuestro proceso de trabajo será el siguiente y lo seguiré rigurosamente:**

1.  **Clarificación Inicial:** Si existe alguna duda o ambigüedad, **preguntar** y solicitar información necesaria _antes_ de plantear cualquier solución.
2.  **Entendimiento del Problema:** Presentar un resumen conciso del problema a resolver.
3.  **Propuesta de Soluciones Teóricas:** Desarrollar y exponer soluciones posibles a nivel _teórico_, detallando pros, contras e implicaciones. _No iniciar implementación en este paso._
4.  **Discusión y Aprobación:** Esperar **"OK" explícito y final** antes de proceder con la implementación.

### 5. Objetividad y Crítica Constructiva

- Ser **completamente objetivo, analítico y crítico**.
- Identificar y proponer la mejor solución técnica, indicar posibles errores, ineficiencias o riesgos, incluso si esto implica contradecir una idea inicial.
- La honestidad y la calidad técnica son primordiales.

### 6. Gestión de Dependencias y Versiones

- **NUNCA instalar dependencias directamente** con `pip install <librería>` sin antes verificar versiones.
- **Proceso obligatorio para nuevas dependencias**:
  1. Verificar la versión actual instalada: `pip show <librería>`
  2. Buscar la última versión disponible: `pip index versions <librería>`
  3. Añadir a `requirements.txt` o `requirements-dev.txt` con versión específica
  4. Instalar desde requirements: `pip install -r requirements.txt`
- **Para versiones existentes**: siempre consultar la versión ya instalada antes de especificar rangos.
- **Versiones específicas vs rangos**: usar versiones específicas (`==x.y.z`) para herramientas críticas, rangos (`>=x.y.z`) solo para dependencias estables.

### 7. Gestión de Documentación

- **NO crear documentación temporal** o de "migración" que no aporte valor a largo plazo.
- **Actualizar documentación existente** en lugar de crear archivos nuevos para cambios.
- **Eliminar documentación obsoleta** cuando se implementen cambios.
- **Documentación debe reflejar el estado actual**, no historial de cambios.

### 8. Política de Limpieza de Archivos Obsoletos

- **Eliminar inmediatamente** archivos, carpetas y configuraciones obsoletas cuando se migre a nuevas herramientas o enfoques.
- **NO mantener "residuos"** como archivos comentados, carpetas backup, o configuraciones "por si acaso".
- **NO dejar historial** en el código base - usar el historial de Git para recuperar versiones anteriores.
- **Ejemplos de eliminación inmediata**:
  - Scripts manuales al migrar a herramientas automatizadas
  - Configuraciones deprecated al actualizar sintaxis
  - Dependencias no utilizadas al optimizar el stack tecnológico
- **Principio**: Mantener el proyecto limpio y enfocado solo en lo que se usa activamente.

## Arquitectura de Microservicios

**Componentes principales:**

- **Simulación** (`run_simulation_provider.py`): SUMO + traci, expone API REST en puerto 5000
- **Decisión** (`run_decision_agent.py`): Agente DQN que consume APIs y controla semáforos
- **Detección** (`run_detection_provider.py`): YOLOv8 para análisis de video (opcional)
- **Reportes** (`run_reporting_service.py`): Métricas y comparaciones

**Flujo de datos:** `Simulación ↔ Decisión ↔ Simulación` (la detección es solo para validación)

## Reglas Críticas

- **Configuración:** TODO viene de `config.yaml` validado por Pydantic en `config_models.py`
- **Para cambiar config:** actualizar `config_models.py` PRIMERO, luego `config.yaml`
- **APIs:** Flask, retornar `return jsonify(data), status_code`
- **Imports:** absolutos desde `src/` - ej: `from src.traffic_system.core.config_loader import load_app_settings`
- **Logging:** usar emojis ✅❌⚠️🧪 y formato estándar del proyecto

## Estructura Clave

```
run_*.py                     # Scripts de inicio
src/traffic_system/
├── api/                     # APIs Flask
├── api_client/             # Clientes para consumir APIs
├── core/config_models.py   # FUENTE DE VERDAD para configuración
├── {decision,simulation,detection}/app.py  # Lógica principal
config.yaml                 # Configuración validada por Pydantic
assets/{dqn_models,sumo_maps,yolo_models}/  # Activos del proyecto
```

## Comandos Esenciales

```bash
# Iniciar sistema
python run_simulation_provider.py  # Terminal 1
python run_decision_agent.py       # Terminal 2

# Testing
python test_sync.py                 # Verificar sincronización
python test_reinicio_api.py         # Probar reinicio

# Calidad de código
pre-commit run --all-files
```

- La lógica de la aplicación para cada componente se encuentra en `src/traffic_system/<nombre_componente>/app.py`.
- Las APIs de Flask están definidas en `src/traffic_system/api/`.
- Los clientes para consumir estas APIs están en `src/traffic_system/api_client/`.

### Activos y Modelos

- **Modelos de Detección (YOLO)**: Se encuentran en `assets/yolo_models/`.
- **Modelos de Decisión (DQN)**: Se guardan en `assets/dqn_models/`.
- **Mapas de Simulación (SUMO)**: Ubicados en `assets/sumo_maps/`.

### Calidad de Código y Herramientas

El proyecto utiliza **pre-commit** para mantener automáticamente la calidad del código:

- **isort**: Organiza imports automáticamente
- **Ruff**: Linter rápido que reemplaza flake8/pylint, con correcciones automáticas
- **Black**: Formateo automático de código (88 caracteres por línea)
- **Mypy**: Verificación de tipos estáticos

Los hooks de pre-commit se ejecutan automáticamente en cada commit. Si detectan problemas, el commit se pausa hasta que se corrijan.

## Flujo de Trabajo del Desarrollador

### Instalación

1. Crea un entorno virtual de Python
2. Instala las dependencias: `pip install -r requirements.txt`
3. Para dependencias de desarrollo: `pip install -r requirements-dev.txt`
4. Configura pre-commit hooks: `pre-commit install`

### Ejecución del Sistema

Para ejecutar el sistema completo, necesitas iniciar cada servicio en un terminal separado:

```bash
# Terminal 1: Iniciar el proveedor de simulación
python run_simulation_provider.py

# Terminal 2: Iniciar el agente de decisión
python run_decision_agent.py
```

**Nota**: El comportamiento de cada script (ej. entrenar vs. inferir, usar video vs. cámara) se controla a través de `config.yaml`.

### Branching y Commits

- Usa **Conventional Commits**: `tipo(ámbito): descripción` (ej. `feat(api): agregar endpoint de reportes`). La descripción debe ser en español, pero los nombres de las ramas y los tipos de commit deben ser en inglés.
- Tipos principales: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- Ramas siguen el patrón: `tipo/descripcion-corta` (ej. `feature/deteccion-ambulancias`)
- Todo el trabajo nuevo debe partir de la rama `develop`

### Pruebas (Testing)

- El proyecto contiene varios scripts de prueba en la raíz, como `test_sync.py` o `test_entrenamiento_dqn_completo.py`.
- Estas son pruebas de integración o funcionales que se ejecutan como scripts individuales: `poetry run python test_sync.py`.
- Al añadir nuevas funcionalidades, considera crear un script de prueba similar para validar la integración de los componentes.

## Documentos de Referencia Adicionales

Para información más detallada, consulta estos documentos específicos:

- **[Guía de Inicio Rápido](../docs/quickstart.md)**: Configuración y comandos esenciales con Poetry
- **[Gestión de Dependencias](../docs/1_setup/dependencies.md)**: Poetry y entornos virtuales
- **[Herramientas de Desarrollo](../docs/2_guides/tooling.md)**: Pre-commit, Black, Ruff, isort, Mypy
- **[Estructura del Proyecto](../docs/1_setup/project_structure.md)**: Arquitectura del código
- **[Guía de Contribución](../docs/2_guides/contributing.md)**: Estándares de desarrollo
