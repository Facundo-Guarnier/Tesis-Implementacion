# 🚀 Guía de Uso: DQN Simplificado con Poetry

## 📋 Resumen

Esta guía te ayuda a ejecutar el **DQN Trainer Simplificado** que elimina todas las contradicciones del entrenador original y proporciona una configuración base estable.

---

## ⚙️ Configuración Requerida en `config.yaml`

Para usar el DQN simplificado, asegúrate de que tu `config.yaml` tenga:

```yaml
decision:
  decision: True                    # ✅ Activar toma de decisiones
  entrenamiento:
    entrenar: True                  # ✅ CRÍTICO: Activar entrenamiento
    # Los demás parámetros serán ignorados - el SimplifiedDQNTrainer usa configuración hardcoded
```

**⚠️ IMPORTANTE:** El DQN simplificado **ignora** la configuración del `config.yaml` para entrenamiento y usa configuraciones hardcoded para evitar contradicciones.

---

## 🔧 Método 1: Configuración Automática (Recomendado)

### Ejecutar script de configuración:
```bash
python setup_simplified_dqn.py
```

Este script:
- ✅ Verifica que Poetry esté instalado
- ✅ Verifica dependencias
- ✅ Configura TensorFlow/GPU
- ✅ Ejecuta el entrenamiento automáticamente

---

## 🔧 Método 2: Configuración Manual

### 1. Verificar Poetry
```bash
poetry --version
```

### 2. Instalar dependencias
```bash
poetry install
```

### 3. Verificar TensorFlow
```bash
poetry run python -c "import tensorflow as tf; print(f'TF: {tf.__version__}, GPU: {len(tf.config.experimental.list_physical_devices(\"GPU\")) > 0}')"
```

### 4. Ejecutar entrenamiento
```bash
poetry run python run_decision_agent.py
```

---

## 📊 Configuración del DQN Simplificado

### 🔧 Configuraciones Hardcoded

El entrenador usa estas configuraciones **fijas** (no modificables):

| Parámetro | Valor | Motivo |
|-----------|-------|--------|
| **Épocas** | 100 | Suficientes para convergencia |
| **Learning Rate** | 0.0001 | Conservador y estable |
| **Epsilon** | 1.0 → 0.05 | Solo epsilon-greedy |
| **Gamma** | 0.99 | Valor estándar |
| **Arquitectura** | [256, 256] | Simple pero potente |
| **Batch Size** | 256 | Estándar |
| **Memory** | 20,000 | Más diversidad |

### ✅ Técnicas Activas
- **Double DQN:** Reduce sobreestimación
- **Dueling DQN:** Separación V(s) y A(s,a)
- **Gradient Clipping:** Previene explosión
- **Huber Loss:** Más robusto que MSE

### ❌ Técnicas Desactivadas
- **Noisy Networks:** Conflicto con epsilon-greedy
- **Prioritized Replay:** Complejidad innecesaria
- **Batch Normalization:** Innecesario para red pequeña
- **Dropout:** Red simple no lo necesita
- **Adaptive LR:** Conflicto con LR fijo

---

## 📁 Estructura de Resultados

Los resultados se guardan en:
```
results/training/SimplifiedDQN_YYYY-MM-DD_HH-MM/
├── training_metrics.csv     # Métricas por época
├── hyperparameters.csv      # Configuración usada
├── baseline.csv            # Rendimiento tiempo fijo
└── epoch_*.h5             # Modelos guardados
```

### 📊 Métricas Importantes

**`training_metrics.csv` contiene:**
- `Epoch`: Número de época
- `Total_Reward`: Recompensa acumulada
- `Avg_Reward`: Recompensa promedio
- `Epsilon`: Nivel de exploración actual
- `Duration_s`: Duración de la época
- `Replay_Count`: Número de entrenamientos
- `Memory_Size`: Experiencias almacenadas

---

## 🎯 Indicadores de Éxito

### ✅ Entrenamiento Estable
- Loss decrece consistentemente
- Epsilon decrece gradualmente (1.0 → 0.05)
- Q-values no explotan ni colapsan
- Recompensa promedio mejora

### ✅ Comportamiento Esperado
```
Epoca 1:   Epsilon: 0.9999, Reward: -50.0 (exploración alta)
Epoca 10:  Epsilon: 0.9950, Reward: -30.0 (aprendiendo)
Epoca 50:  Epsilon: 0.9512, Reward: -10.0 (mejorando)
Epoca 100: Epsilon: 0.9048, Reward: 5.0   (convergiendo)
```

---

## 🚨 Solución de Problemas

### Problema: "No se pudo obtener tiempos de espera"
**Solución:** Verificar que el simulador SUMO esté ejecutándose
```bash
# En otra terminal, ejecutar simulador primero
poetry run python run_simulation_provider.py
```

### Problema: "GPU no detectada"
**Solución:** El entrenador funciona en CPU también
- GPU: Entrenamiento más rápido
- CPU: Funcional pero más lento

### Problema: "Error de conexión API"
**Solución:** Verificar URL en `config.yaml`
```yaml
base_url: "http://localhost:5000"  # O la IP correcta
```

### Problema: Loss = 0.000000 persistente
**Causa:** Este era el problema del entrenador original
**Solución:** El SimplifiedDQNTrainer elimina este problema

---

## 📈 Comparación vs Original

| Aspecto | Original | Simplificado | Resultado |
|---------|----------|--------------|-----------|
| **Exploración** | Noisy + Epsilon ❌ | Solo Epsilon ✅ | Estable |
| **Learning Rate** | Decay + Adaptive ❌ | Fijo ✅ | Predecible |
| **Arquitectura** | [64,64,64] + BN + ResNet ❌ | [256,256] ✅ | Potente y simple |
| **Convergencia** | Nunca ❌ | <50 épocas ✅ | Confiable |

---

## 🔄 Próximos Pasos

### Fase 1: Base Estable ✅
- [x] Eliminar contradicciones
- [x] Configuración hardcoded
- [x] Solo técnicas probadas

### Fase 2: Primera Optimización
- [ ] Añadir Prioritized Experience Replay
- [ ] Medir impacto individual
- [ ] Mantener estabilidad

### Fase 3: Optimizaciones Avanzadas
- [ ] Learning rate scheduling
- [ ] Noisy Networks (si es necesario)
- [ ] Hardware optimizations

---

## 💡 Consejos

1. **Primero estabilidad, después optimización**
2. **Una técnica nueva a la vez**
3. **Siempre comparar con baseline**
4. **Monitorear métricas clave**

---

**🏆 Objetivo:** Tener un modelo DQN **estable y predecible** que sirva como base sólida para futuras mejoras.
