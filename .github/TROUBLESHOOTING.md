# Troubleshooting Guide

Guía para resolver problemas comunes en el desarrollo.

## 🚨 Problemas de Simulación

### Error: "No se puede conectar a SUMO"

**Síntomas**: `FatalTraCIError` al iniciar simulación

**Soluciones**:

1. Verificar instalación SUMO: `sumo-gui --version`
2. Revisar rutas en `config.yaml`:
   ```yaml
   sumo:
     path_sumo: "/usr/share/sumo" # Linux
     # O "C:/Program Files/SUMO"   # Windows
   ```
3. Verificar archivos de mapa:
   ```powershell
   ls assets/sumo_maps/MapaDe0/
   # Debe contener: mapa.sumocfg, red.net.xml, routes.rou.xml
   ```

### Error: "Simulaciones desincronizadas"

**Síntomas**: `{"error": "Las simulaciones están desincronizadas"}`

**Soluciones**:

1. Verificar sincronización: `GET /sincronizacion`
2. Reiniciar simulaciones: `POST /simulacion/reiniciar`
3. En casos extremos, reiniciar el servidor

**Debug**:

```python
import requests
resp = requests.get("http://127.0.0.1:5000/sincronizacion")
print(resp.json())
# Debe mostrar diferencia ≤ 1.0s
```

### Simulación se "cuelga"

**Síntomas**: Endpoints no responden, GUI de SUMO congelada

**Soluciones**:

1. Cerrar procesos: `Ctrl+C` en terminals
2. Verificar puertos: `netstat -an | findstr 5000`
3. Reiniciar con configuración mínima:
   ```yaml
   sumo:
     gui: False
     comparar: False
   ```

## 🧠 Problemas del Agente DQN

### Error: "No se puede cargar el modelo"

**Síntomas**: `FileNotFoundError` o modelo corrupto

**Soluciones**:

1. Verificar ruta en `config.yaml`:
   ```yaml
   decision:
     path_modelo_entrenado: "assets/dqn_models/modelo.h5"
   ```
2. Verificar que el archivo existe:
   ```powershell
   ls assets/dqn_models/
   ```
3. Si no existe, entrenar nuevo modelo:
   ```yaml
   decision:
     entrenamiento:
       entrenar: True
   ```

### Entrenamiento muy lento

**Síntomas**: Épocas tardan más de 10 minutos

**Soluciones**:

1. Verificar GPU: `python test_verificar_gpu.py`
2. Reducir parámetros en `config.yaml`:
   ```yaml
   entrenamiento:
     num_epocas: 10 # Reducir de 25
     batch_size: 32 # Reducir de 64
     memory: 2000 # Reducir de 4000
   ```
3. Usar modelo más simple:
   ```yaml
   hidden_layers: [64, 64] # En lugar de [512, 512, ...]
   ```

### Agente toma decisiones erráticas

**Síntomas**: Cambios constantes de semáforos, no converge

**Soluciones**:

1. Verificar epsilon en `config.yaml`:
   ```yaml
   entrenamiento:
     epsilon: 0.1 # Reducir exploración
     epsilon_min: 0.01
   ```
2. Aumentar gamma (consideración de recompensas futuras):
   ```yaml
   gamma: 0.95 # De 0.85 a 0.95
   ```
3. Verificar que el modelo está en modo inferencia:
   ```yaml
   entrenamiento:
     entrenar: False
   ```

## 🌐 Problemas de API

### Error: "Connection refused"

**Síntomas**: `requests.ConnectionError`

**Soluciones**:

1. Verificar que el servidor está ejecutándose:
   ```powershell
   python run_simulation_provider.py
   ```
2. Probar conexión básica:
   ```powershell
   curl http://127.0.0.1:5000/simulacion
   ```
3. Verificar puerto en `config.yaml`:
   ```yaml
   base_url: "http://127.0.0.1:5000"
   ```

### Error 500: "Error interno"

**Síntomas**: Endpoints retornan errores 500

**Soluciones**:

1. Revisar logs del servidor en la terminal
2. Verificar que SUMO está respondiendo
3. Probar endpoint simple primero: `/simulacion`

### Timeouts en requests

**Síntomas**: `requests.Timeout`

**Soluciones**:

1. Aumentar timeout en clientes:
   ```python
   response = requests.get(url, timeout=30)  # De 5 a 30
   ```
2. Verificar carga del sistema (CPU/memoria)
3. Reducir steps por request:
   ```python
   api.advance_simulation(steps=5)  # En lugar de 10+
   ```
4. Verificar que SUMO no está colgado o si la GUI está en pausa o congelada.

## 🔧 Problemas de Configuración

### Error: "Archivo config.yaml tiene errores"

**Síntomas**: `ConfigValidationError`

**Soluciones**:

1. Verificar sintaxis YAML:
   ```powershell
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```
2. Comparar con `config_models.py` para campos requeridos
3. Verificar tipos de datos (bool, int, str, list)

### Modelo Pydantic no reconoce nueva configuración

**Síntomas**: Campo ignorado o error de validación

**Soluciones**:

1. Actualizar `src/traffic_system/core/config_models.py`
2. Añadir campo al modelo correspondiente:
   ```python
   class DecisionSettings(BaseModel):
       nuevo_campo: int  # Añadir aquí
   ```
3. Reiniciar la aplicación

## 🛠️ Problemas de Desarrollo

### Pre-commit hooks fallan

**Síntomas**: Commit cancelado por herramientas

**Soluciones**:

1. Ejecutar herramientas manualmente:
   ```powershell
   black src/
   ruff check src/ --fix
   mypy src/
   ```
2. Verificar configuración:
   ```powershell
   git config --get core.hooksPath
   # Debe ser: .githooks
   ```

### ImportError en módulos locales

**Síntomas**: `ModuleNotFoundError: No module named 'src'`

**Soluciones**:

1. Ejecutar desde raíz del proyecto
2. Verificar estructura de `__init__.py`
3. Usar rutas absolutas en imports:
   ```python
   from src.traffic_system.core.config_loader import load_app_settings
   ```

## 📋 Checklist de Diagnóstico

Antes de reportar un problema, verificar:

- [ ] SUMO instalado y accesible
- [ ] Puerto 5000 disponible
- [ ] `config.yaml` válido
- [ ] Archivos de simulación en `assets/sumo_maps/MapaDe0/`
- [ ] Dependencias instaladas: `poetry install`
- [ ] Ejecutando desde directorio raíz del proyecto
- [ ] Logs del servidor para errores específicos

## 🆘 Obtener Ayuda

1. **Revisar logs**: Siempre ejecutar con logs visibles
2. **Probar scripts**: Usar `test_sync.py` para verificar estado
3. **Configuración mínima**: Probar con opciones básicas
4. **Información del sistema**: Versiones de Python, SUMO, dependencies
