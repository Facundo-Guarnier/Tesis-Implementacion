# Configuración de GPU para Entrenamiento DQN

Esta guía te ayudará a configurar tu sistema para entrenar el modelo DQN usando GPU, lo que puede acelerar significativamente el proceso de entrenamiento.

## 🚀 Ventajas del entrenamiento en GPU

- **⚡ Velocidad**: 10-100x más rápido que CPU para modelos de deep learning
- **🔄 Paralelización**: Procesamiento masivo en paralelo de operaciones matriciales
- **💾 Memoria**: Acceso más rápido a grandes cantidades de datos
- **🎯 Eficiencia**: Mejor utilización de recursos computacionales

## 📋 Requisitos previos

### 1. Hardware necesario

- **GPU NVIDIA** compatible con CUDA (Series GTX 10xx o superior, RTX series recomendada)
- **Memoria GPU**: Mínimo 4GB, recomendado 8GB o más
- **Drivers**: Drivers NVIDIA actualizados

### 2. Software necesario

- **CUDA Toolkit** (versión compatible con TensorFlow)
- **cuDNN** (biblioteca de deep learning de NVIDIA)
- **TensorFlow** con soporte GPU

## 🔧 Instalación paso a paso

### Paso 1: Verificar tu GPU

```bash
# En Windows
nvidia-smi

# Verificar compatibilidad CUDA
# Tu GPU debe aparecer en: https://developer.nvidia.com/cuda-gpus
```

### Paso 2: Instalar CUDA Toolkit

1. Visita: https://developer.nvidia.com/cuda-downloads
2. Selecciona tu sistema operativo
3. Descarga e instala CUDA Toolkit 11.8 o 12.x
4. Reinicia tu sistema

### Paso 3: Instalar cuDNN

1. Visita: https://developer.nvidia.com/cudnn
2. Registrarte/iniciar sesión (gratis)
3. Descargar cuDNN compatible con tu versión de CUDA
4. Extraer y copiar archivos a directorio CUDA

### Paso 4: Instalar TensorFlow con soporte GPU

```bash
# Opción 1: TensorFlow con CUDA (recomendado)
pip install tensorflow[and-cuda]

# Opción 2: Versión específica
pip install tensorflow-gpu==2.13.0

# Verificar instalación
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

## 🧪 Verificación de configuración

Ejecuta el script de verificación incluido:

```bash
python test_verificar_gpu.py
```

Este script verificará:

- ✅ Instalación de TensorFlow
- ✅ Disponibilidad de GPU
- ✅ Configuración CUDA/cuDNN
- ✅ Test de entrenamiento

## 🎯 Cambios implementados en el código

### Configuración automática de GPU

El código ahora incluye:

```python
def __setup_gpu(self) -> None:
    """Configura automáticamente GPU si está disponible"""
    # Detecta y configura GPUs
    # Configura crecimiento dinámico de memoria
    # Optimiza para múltiples GPUs si están disponibles
```

### Optimizaciones específicas para GPU

- **Crecimiento dinámico de memoria**: Evita ocupar toda la VRAM
- **Estrategia de distribución**: Soporte para múltiples GPUs
- **Dispositivos específicos**: Fuerza operaciones en GPU cuando es posible
- **Batch processing**: Optimizado para procesamiento en lotes en GPU

### Logging mejorado

- 🚀 Indica si está usando GPU o CPU
- 📊 Muestra información detallada de la GPU
- 🔧 Reporta configuración de memoria y distribución

## 📈 Esperando mejoras de rendimiento

### Entrenamiento típico en CPU vs GPU:

| Métrica           | CPU (Intel i7) | GPU (RTX 3070) | Mejora                |
| ----------------- | -------------- | -------------- | --------------------- |
| Tiempo por época  | ~45 minutos    | ~3-5 minutos   | **9-15x**             |
| Memoria utilizada | 8-16 GB RAM    | 4-6 GB VRAM    | Más eficiente         |
| Utilización       | 60-80%         | 90-95%         | Mejor aprovechamiento |

## 🐛 Solución de problemas comunes

### Error: "No se encontraron GPUs"

```bash
# Verificar drivers
nvidia-smi

# Reinstalar TensorFlow
pip uninstall tensorflow
pip install tensorflow[and-cuda]
```

### Error de memoria GPU

```python
# El código incluye crecimiento dinámico automático
# Si persiste, ajusta batch_size en config.yaml:
decision:
  entrenamiento:
    batch_size: 32  # Reducir si hay errores de memoria
```

### Error: "CUDA out of memory"

1. **Reducir batch_size** en configuración
2. **Cerrar otras aplicaciones** que usen GPU
3. **Reiniciar** para limpiar memoria GPU

### Conflictos con otras versiones de CUDA

```bash
# Usar entorno virtual
python -m venv gpu_env
gpu_env\Scripts\activate  # Windows
pip install tensorflow[and-cuda]
```

## 🎮 Configuración específica por GPU

### RTX 30xx/40xx Series

```yaml
# config.yaml - Configuración optimizada
decision:
  entrenamiento:
    batch_size: 128 # Aprovechar memoria abundante
    memory: 8000 # Memoria de replay más grande
    hidden_layers: [64, 64, 32] # Redes más grandes
```

### GTX 10xx Series

```yaml
# config.yaml - Configuración conservadora
decision:
  entrenamiento:
    batch_size: 64 # Memoria más limitada
    memory: 4000 # Memoria de replay moderada
    hidden_layers: [32, 32, 16] # Redes más pequeñas
```

## 📊 Monitoreo durante entrenamiento

### GPU utilization

```bash
# Mientras entrena, ejecutar en otra terminal:
nvidia-smi -l 1  # Actualización cada segundo
```

### Logs del entrenamiento

El código ahora muestra:

```
🚀 GPU encontrada(s): 1
✅ Configuración GPU: Crecimiento dinámico de memoria habilitado
🧠 Modelo creado con estrategia: DefaultStrategy
🎯 Modelo funcionando correctamente en: /job:localhost/replica:0/task:0/device:GPU:0
```

## 🚀 Ejecutar entrenamiento con GPU

Una vez configurado, simplemente ejecuta el entrenamiento normal:

```bash
# El código automáticamente detectará y usará GPU
python run_decision_agent.py

# O directamente el entrenamiento
python -c "
from src.traffic_system.decision.DQN.EntrenamientoDQN import EntrenamientoDQN
trainer = EntrenamientoDQN()
trainer.main()
"
```

## 💡 Consejos adicionales

### Optimización del rendimiento

1. **Batch size**: Incrementa gradualmente hasta encontrar el óptimo
2. **Memoria de replay**: Más grande = mejor, pero consume más VRAM
3. **Arquitectura de red**: Redes más profundas aprovechan mejor la GPU

### Monitoreo

- Usa `nvidia-smi` para monitorear uso de GPU
- Los logs te dirán exactamente qué dispositivo se está usando
- El script `verificar_gpu.py` valida tu configuración

### Backup de modelos

```python
# Los modelos se guardan automáticamente por época
# Ubicación: results/training/DQN_YYYY-MM-DD_HH-MM/
```

¡Con esta configuración, tu entrenamiento DQN debería ser mucho más rápido! 🎉
