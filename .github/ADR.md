# Architecture Decision Records

Documentación de decisiones arquitectónicas importantes del proyecto.

## ADR-001: Arquitectura de Microservicios

**Estado**: Aceptado  
**Fecha**: 2025

### Contexto

El sistema necesita separar las responsabilidades entre detección, simulación, decisión y reportes.

### Decisión

Implementar arquitectura de microservicios con APIs REST para comunicación entre componentes.

### Consecuencias

- ✅ Separación clara de responsabilidades
- ✅ Posibilidad de ejecutar componentes independientemente
- ✅ Escalabilidad individual de componentes
- ❌ Complejidad adicional de comunicación
- ❌ Manejo de errores de red requerido

---

## ADR-002: Configuración Centralizada con Pydantic

**Estado**: Aceptado  
**Fecha**: 2025

### Contexto

Necesidad de configuración type-safe y validada para todos los componentes.

### Decisión

Usar `config.yaml` como fuente única de verdad, validado por modelos Pydantic en `config_models.py`.

### Consecuencias

- ✅ Validación automática de configuración
- ✅ Type hints y autocompletado
- ✅ Errores claros en configuración incorrecta
- ✅ Configuración centralizada
- ❌ Requiere actualizar modelos para nuevas configuraciones

---

## ADR-003: Simulaciones Paralelas para Comparación

**Estado**: Aceptado  
**Fecha**: 2025

### Contexto

Necesidad de comparar rendimiento entre diferentes estrategias de control.

### Decisión

Ejecutar dos simulaciones SUMO simultáneas (S1 controlada por IA, S2 con control fijo).

### Consecuencias

- ✅ Comparación directa de estrategias
- ✅ Métricas de rendimiento cuantificables
- ❌ Mayor consumo de recursos
- ❌ Complejidad de sincronización temporal

---

## ADR-004: DQN para Toma de Decisiones

**Estado**: Aceptado  
**Fecha**: 2025

### Contexto

Necesidad de un agente inteligente para optimizar fases de semáforos.

### Decisión

Implementar Deep Q-Network con TensorFlow/Keras para el agente de decisión.

### Consecuencias

- ✅ Aprendizaje adaptativo
- ✅ Optimización basada en recompensas
- ✅ Capacidad de manejar estados complejos
- ❌ Tiempo de entrenamiento significativo
- ❌ Requiere ajuste de hiperparámetros

---

## ADR-005: Scripts de Prueba como Tests de Integración

**Estado**: Aceptado  
**Fecha**: 2025

### Contexto

Necesidad de validar interacciones entre componentes del sistema.

### Decisión

Crear scripts ejecutables (`test_*.py`) que prueban flujos completos del sistema.

### Consecuencias

- ✅ Pruebas de extremo a extremo
- ✅ Validación de APIs reales
- ✅ Fácil ejecución manual
- ❌ No integrado con frameworks de testing tradicionales
- ❌ Require servicios ejecutándose

---

## ADR-006: Detección como Componente Opcional

**Estado**: Aceptado  
**Fecha**: 2025

### Contexto

La detección por video es principalmente para validación, no para el flujo principal.

### Decisión

El agente de decisión consume datos de la simulación, no de detección en tiempo real.

### Consecuencias

- ✅ Sistema funcional sin cámaras físicas
- ✅ Entrenamiento más rápido y confiable
- ✅ Menos dependencias de hardware
- ❌ Limitada validación con datos reales
- ❌ Gap entre simulación y realidad

---

## ADR-007: Flask para APIs REST

**Estado**: Aceptado  
**Fecha**: 2025

### Contexto

Necesidad de APIs simples para comunicación entre componentes.

### Decisión

Usar Flask para crear APIs REST ligeras en cada componente.

### Consecuencias

- ✅ Simplicidad y rapidez de desarrollo
- ✅ Flexibilidad en diseño de endpoints
- ✅ Fácil debugging y testing
- ❌ Menos características que FastAPI
- ❌ Sin documentación automática de API
