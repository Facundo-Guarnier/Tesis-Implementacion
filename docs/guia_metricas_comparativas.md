# 📊 Guía de Uso - Sistema de Métricas Comparativas DQN vs Tiempos Fijos

Esta guía explica cómo obtener las 3 métricas clave para demostrar la eficacia del sistema DQN.

## 🎯 Métricas Objetivo

### 1. **Recompensa Acumulada** - Valida el aprendizaje del agente DQN
### 2. **Tiempo de Espera Acumulado** - Impacto real en conductores
### 3. **Promedio de Vehículos en Sistema** - Medición de congestión

---

## ⚙️ Configuración Requerida

### 1. Editar `config.yaml`:

```yaml
sumo:
  comparar: true  # ✅ ACTIVAR modo comparación
  use_random_seed: false  # ✅ RECOMENDADO para resultados reproducibles
  fixed_seed: 12345  # ✅ Opcional: usar semilla específica

decision:
  decision: true  # ✅ ACTIVAR agente de decisión
  path_modelo_entrenado: "assets/dqn_models/tu_modelo.h5"  # ✅ Modelo DQN entrenado
```

### 2. Verificar que tienes:
- ✅ SUMO instalado y funcionando
- ✅ Modelo DQN entrenado (archivo .h5 o .keras)
- ✅ Configuración de rutas y zonas correcta

---

## 🚀 Ejecución

### Paso 1: Iniciar Simulación
```bash
python run_simulation_provider.py
```
**Esperar hasta ver:** `Simulaciones con diferencia inicial aceptable`

### Paso 2: Iniciar Agente DQN
```bash
python run_decision_agent.py
```
**Esperar hasta que la simulación termine naturalmente** (según `simulation_time_limit`)

---

## 📈 Interpretación de Resultados

### 🏆 Métrica 1: Recompensa Acumulada (Logs de Decisión)
```
🏆 === RESUMEN FINAL - RECOMPENSA ACUMULADA DQN ===
📊 Recompensa Total DQN: +1,234.56
📊 Pasos de Decisión: 180
📊 Recompensa Promedio por Paso: +6.86
```

**Para tu presentación:**
- "El sistema DQN logró una recompensa acumulada de **+1,234.56**, superando el baseline de tiempos fijos"
- (Necesitas ejecutar simulación con tiempos fijos por separado para obtener la comparación)

### ⏱️ Métrica 2: Tiempo de Espera Acumulado (Logs de Simulación)
```
📈 === RESUMEN FINAL - MÉTRICAS COMPARATIVAS ===
⏱️  TIEMPO DE ESPERA ACUMULADO:
    S1 (DQN): 1,245.30s | S2 (Tiempos Fijos): 1,567.80s
    ✅ Reducción DQN: -322.50s (-20.6%)
```

**Para tu presentación:**
- "El sistema DQN redujo el tiempo total de espera en **322.5 segundos**, una **mejora del 20.6%**"

### 🚗 Métrica 3: Promedio Vehículos en Sistema (Logs de Simulación)
```
🚗 PROMEDIO VEHÍCULOS EN SISTEMA:
    S1 (DQN): 15.2 | S2 (Tiempos Fijos): 18.7
    ✅ Reducción DQN: -3.5 (-18.7%)
```

**Para tu presentación:**
- "El sistema mantuvo un promedio de **15.2 vehículos** simultáneos vs **18.7** con tiempos fijos, reduciendo la congestión en **18.7%**"

---

## 🔧 Troubleshooting

### ❌ No aparece "RESUMEN FINAL - MÉTRICAS COMPARATIVAS"
- Verificar que `sumo.comparar: true` en config.yaml
- Confirmar que ambas simulaciones S1 y S2 se iniciaron correctamente
- Buscar logs: "Modo de comparación habilitado"

### ❌ No aparece "RESUMEN FINAL - RECOMPENSA ACUMULADA DQN"
- Verificar que `decision.decision: true` en config.yaml
- Confirmar que el modelo DQN existe en la ruta configurada
- Verificar que el agente de decisión se conectó correctamente

### ❌ Simulaciones desincronizadas
- Usar `sumo.use_random_seed: false` para determinismo
- Verificar que ambas simulaciones usan la misma semilla
- Buscar logs: "Simulaciones perfectamente sincronizadas"

---

## 📋 Script de Validación Rápida

```bash
python test_metricas_comparativas.py
```

Este script verifica:
- ✅ Configuración correcta
- ✅ Modelo DQN disponible
- ✅ Instrucciones detalladas
- ✅ Criterios de interpretación

---

## 💡 Tips para Presentaciones

### Formato Sugerido:
1. **Métrica 1 - Recompensa Acumulada**: "Valida que el agente aprendió correctamente"
2. **Métrica 2 - Tiempo de Espera**: "Beneficio directo para conductores"
3. **Métrica 3 - Congestión**: "Mejora en fluidez del tráfico"

### Frases de Impacto:
- "El sistema DQN **redujo los tiempos de espera en X%**, beneficiando directamente a los conductores"
- "La **reducción de congestión del Y%** demuestra mayor eficiencia en la gestión del tráfico"
- "La **recompensa acumulada superior** valida que el agente aprendió estrategias óptimas"

---

## 🎯 Criterios de Éxito

### ✅ Sistema Funcional:
- Las 3 métricas aparecen en los logs
- Los cálculos de mejora porcentual son coherentes
- DQN muestra mejoras en al menos 2 de las 3 métricas

### ✅ Listo para Presentación:
- Tienes los números específicos de mejora
- Puedes explicar el significado de cada métrica
- Los resultados demuestran ventajas del DQN vs tiempos fijos
