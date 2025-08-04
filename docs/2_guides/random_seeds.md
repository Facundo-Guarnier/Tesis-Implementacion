# 🎲 Configuración de Semillas Aleatorias en SUMO

Esta guía explica los 3 nuevos ajustes para controlar la aleatoriedad en las simulaciones SUMO.

## ⚙️ Configuración Disponible

### `use_random_seed: True/False`
- **`False`**: Usa comportamiento determinístico de SUMO
- **`True`**: Genera semilla aleatoria basada en tiempo actual del sistema

### `fixed_seed: number/null`
- **`null`**: Usa semilla por defecto de SUMO (23423)
- **`12345`**: Usa semilla específica para reproducibilidad exacta

### `persist_random_seed: True/False`
- **`True`**: Reutiliza la misma semilla aleatoria en todos los reinicios
- **`False`**: Genera nueva semilla aleatoria en cada reinicio

## 🎯 Casos de Uso

### 🔄 Reproducibilidad Total
```yaml
use_random_seed: False
fixed_seed: 12345
```
✅ **Resultado**: Simulaciones idénticas siempre

### 🎲 Variabilidad Controlada (Recomendado para RL)
```yaml
use_random_seed: True
persist_random_seed: True
```
✅ **Resultado**: Una semilla aleatoria, consistente entre reinicios

### 🎰 Máxima Variabilidad
```yaml
use_random_seed: True
persist_random_seed: False
```
⚠️ **Resultado**: Cada reinicio completamente diferente

## 💡 Recomendaciones

- **Entrenamiento RL**: `use_random_seed: True, persist_random_seed: True`
- **Evaluación/Comparación**: `use_random_seed: False, fixed_seed: 12345`
- **Depuración**: `use_random_seed: False, fixed_seed: 12345`
