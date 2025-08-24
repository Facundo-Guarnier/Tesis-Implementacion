# Plan de Implementación - Sistema de Métricas Comparativas DQN vs Tiempos Fijos

## Objetivos
Implementar un sistema robusto para calcular y comparar las tres métricas clave que demuestran la eficacia del sistema DQN:

1. **Recompensa Acumulada** - Validar el aprendizaje del agente DQN
2. **Tiempo de Espera Acumulado** - Impacto real en conductores
3. **Promedio de Vehículos en Sistema** - Medición de congestión

## Contexto Técnico
- **SUMO ya implementa** comparación en vivo mediante `ComparisonLogger` con logs en consola
- **DQNEvaluator existe** pero se enfoca en métricas de entrenamiento
- **Sistema de reportes** disponible pero necesita extensión para métricas comparativas
- **Configuración dual** S1 (DQN API) vs S2 (tiempos fijos) ya funciona

---

## 📋 Plan de Tareas - SIMPLIFICADO

### FASE 1: Implementación Core (Métricas Separadas)

- [x] 1.1 Extender ComparisonLogger (Lado Simulación)
  - ✅ Acumular tiempo de espera total S1 vs S2 durante toda la simulación
  - ✅ Acumular suma/promedio de vehículos S1 vs S2 en tiempo real
  - ✅ Añadir resumen final con mejoras porcentuales al terminar

- [x] 1.2 Extender DQNModel.run_inference (Lado Decisión)
  - ✅ Acumular recompensa total durante inferencia con modelo DQN
  - ✅ Al final, mostrar resumen de recompensa acumulada con instrucciones de comparación
  - ✅ Implementar cálculo de recompensa usando misma lógica que entrenamiento

- [x] 1.3 Verificar configuración de semillas
  - ✅ Confirmar que S1 y S2 usan la misma semilla en modo comparación
  - ✅ Sistema ya implementado correctamente en start_traci_connection()

### FASE 2: Validación y Testing

- [x] 2.1 Crear script de validación
  - ✅ Script para probar el sistema completo con sumo.comparar: true
  - ✅ Verificar que las 3 métricas se calculan y muestran correctamente
  - ✅ Confirmar que los porcentajes de mejora son coherentes

- [x] 2.2 Documentación básica
  - ✅ Actualizar documentación sobre cómo obtener las métricas
  - ✅ Ejemplos de interpretación de resultados
  - ✅ Instrucciones de uso para presentaciones

---

## 🎯 Estructura de Output Objetivo

### Métrica 1: Recompensa Acumulada (Logs de Decisión)
```
🏆 === RESUMEN RECOMPENSA ACUMULADA ===
📊 DQN (Inferencia): +1,234.56
📊 Tiempos Fijos (Baseline): +987.65
✅ Mejora DQN: +246.91 (+25.0%)
```

### Métrica 2 y 3: Tiempo de Espera + Vehículos (Logs de Simulación)
```
📈 === RESUMEN MÉTRICAS COMPARATIVAS ===
⏱️  TIEMPO DE ESPERA TOTAL:
    S1 (DQN): 1,245.30s | S2 (Fijo): 1,567.80s
    ✅ Reducción: -322.50s (-20.6%)

🚗 PROMEDIO VEHÍCULOS EN SISTEMA:
    S1 (DQN): 15.2 | S2 (Fijo): 18.7
    ✅ Reducción: -3.5 (-18.7%)
```

### FASE 3: Implementación del Sistema de Métricas Comparativas

- [ ] 3.1 Crear módulo `metrics_collector.py`
  - Implementar `MetricsCollector` para capturar datos en tiempo real
  - Definir estructura de datos para las 3 métricas objetivo
  - Integrar con APIs de simulación existentes
  - _Requirements: Type safety, logging con emojis_

- [ ] 3.2 Crear módulo `comparative_analyzer.py`
  - Implementar `ComparativeAnalyzer` para procesar y comparar métricas
  - Calcular mejoras porcentuales entre DQN y tiempos fijos
  - Generar estadísticas descriptivas (media, desviación, percentiles)
  - _Requirements: Análisis estadístico robusto_

- [ ] 3.3 Crear módulo `metrics_exporter.py`
  - Implementar `MetricsExporter` para generar reportes
  - Soporte para múltiples formatos (CSV, JSON, markdown)
  - Templates para presentación profesional de resultados
  - _Requirements: Flexibilidad de formato, documentación clara_

### FASE 4: Integración con Sistema Existente

- [ ] 4.1 Extender ComparisonLogger
  - Integrar `MetricsCollector` en el flujo de comparación actual
  - Mantener compatibilidad con logs de consola existentes
  - Añadir captura estructurada de datos para análisis posterior
  - _Requirements: Backwards compatibility_

- [ ] 4.2 Integrar con DQNEvaluator
  - Conectar métricas de recompensa acumulada con sistema comparativo
  - Sincronizar datos de entrenamiento con métricas de simulación
  - Añadir métricas comparativas a evaluación de época
  - _Requirements: Coherencia temporal, sincronización de datos_

- [ ] 4.3 Actualizar sistema de reportes
  - Extender `ReportingService` para incluir métricas comparativas
  - Integrar con `ComparativeAnalyzer` y `MetricsExporter`
  - Añadir endpoints API para consulta de métricas en tiempo real
  - _Requirements: API REST, DTOs con Pydantic_

### FASE 5: Automatización y Flujos de Trabajo

- [ ] 5.1 Crear script de comparación automática
  - Script `run_comparative_analysis.py` para análisis completo
  - Automatizar secuencia: entrenamiento → evaluación → comparación → reporte
  - Integrar con sistema de configuración existente
  - _Requirements: Poetry compatibility, logging estándar_

- [ ] 5.2 Implementar métricas en tiempo real
  - Dashboard simple para monitoreo durante simulación
  - Alertas cuando alguna métrica muestra degradación significativa
  - Integración opcional con sistema de reportes web
  - _Requirements: Performance mínimo, datos en tiempo real_

### FASE 6: Validación y Testing

- [ ] 6.1 Crear tests unitarios
  - Tests para `MetricsCollector`, `ComparativeAnalyzer`, `MetricsExporter`
  - Mocks para APIs de simulación y datos de prueba
  - Validación de cálculos estadísticos y formatos de salida
  - _Requirements: Coverage >80%, pytest_

- [ ] 6.2 Crear tests de integración
  - Test completo de flujo comparativo DQN vs tiempos fijos
  - Validar sincronización de datos entre componentes
  - Verificar coherencia de métricas entre diferentes formatos
  - _Requirements: Simulación real, datos consistentes_

- [ ] 6.3 Crear script de validación de métricas
  - Script `test_metricas_comparativas.py` para validación rápida
  - Verificar que las 3 métricas se calculan correctamente
  - Comparar resultados con cálculos manuales de referencia
  - _Requirements: Validación cruzada, documentación de casos_

### FASE 7: Documentación y Entrega

- [ ] 7.1 Actualizar documentación técnica
  - Documentar nuevas configuraciones en guías existentes
  - Añadir ejemplos de uso y interpretación de métricas
  - Actualizar `docs/3_reference/` con especificaciones completas
  - _Requirements: Coherencia con documentación existente_

- [ ] 7.2 Crear guía de interpretación de resultados
  - Documento explicando significado de cada métrica
  - Criterios para determinar si DQN supera a tiempos fijos
  - Ejemplos de interpretación para diferentes escenarios
  - _Requirements: Claridad para audiencia técnica y no técnica_

- [ ] 7.3 Crear templates de presentación
  - Templates markdown para reportes de investigación
  - Formatos para presentación de resultados académicos
  - Gráficos y visualizaciones estándar para cada métrica
  - _Requirements: Profesionalismo, facilidad de uso_

### FASE 8: Optimización y Mejoras

- [ ] 8.1 Optimizar performance de captura de métricas
  - Minimizar overhead en tiempo de simulación
  - Implementar caching inteligente de datos frecuentes
  - Optimizar frecuencia de cálculo según necesidades
  - _Requirements: <5% overhead, configurabilidad_

- [ ] 8.2 Implementar análisis estadístico avanzado
  - Pruebas de significancia estadística (t-test, Mann-Whitney)
  - Intervalos de confianza para mejoras porcentuales
  - Análisis de varianza y estabilidad de resultados
  - _Requirements: Rigor estadístico, interpretabilidad_

---

## 🎯 Métricas de Éxito

### Funcionalidad Core
- [ ] Las 3 métricas se calculan automáticamente en cada comparación
- [ ] Reportes se generan en formato CSV, JSON y markdown
- [ ] Integración completa con flujo de entrenamiento existente

### Calidad y Rendimiento
- [ ] Overhead de captura de métricas <5% del tiempo total de simulación
- [ ] Tests cubren >80% del código de métricas
- [ ] Documentación completa y ejemplos de uso funcionales

### Presentación de Resultados
- [ ] Formato profesional apto para presentación académica
- [ ] Cálculos de mejora porcentual automáticos y precisos
- [ ] Interpretación clara del significado de cada métrica

---

## 🔧 Consideraciones Técnicas

### Arquitectura
- **Mantener separación de responsabilidades**: Colector, Analizador, Exportador
- **Integración no invasiva**: No romper funcionalidad existente
- **Configurabilidad**: Permitir habilitar/deshabilitar métricas específicas

### Performance
- **Captura eficiente**: Minimizar llamadas API adicionales
- **Procesamiento asíncrono**: No bloquear simulación principal
- **Caching inteligente**: Evitar recálculos innecesarios

### Calidad de Código
- **Type safety**: Pydantic para todos los modelos de datos
- **Logging consistente**: Usar sistema de logging estándar con emojis
- **Testing robusto**: Tests unitarios y de integración completos

### Documentación
- **Actualización simultánea**: Documentar mientras se implementa
- **Ejemplos prácticos**: Casos de uso reales y interpretación
- **Coherencia**: Mantener estilo con documentación existente

---

## 📊 Estructura de Datos Objetivo

### Métrica 1: Recompensa Acumulada
```python
RecompensaAcumulada = {
    "dqn_total": float,
    "tiempos_fijos_total": float,
    "mejora_absoluta": float,
    "mejora_porcentual": float,
    "episodios_comparados": int
}
```

### Métrica 2: Tiempo de Espera Acumulado
```python
TiempoEsperaAcumulado = {
    "dqn_total_segundos": float,
    "tiempos_fijos_total_segundos": float,
    "reduccion_absoluta": float,
    "reduccion_porcentual": float,
    "vehiculos_considerados": int
}
```

### Métrica 3: Promedio de Vehículos en Sistema
```python
PromedioVehiculosSistema = {
    "dqn_promedio": float,
    "tiempos_fijos_promedio": float,
    "reduccion_congestion": float,
    "reduccion_porcentual": float,
    "mediciones_tomadas": int
}
```
