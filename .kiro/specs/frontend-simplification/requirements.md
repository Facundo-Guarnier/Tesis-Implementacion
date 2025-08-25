# Requirements Document

## Introduction

El frontend actual del sistema de tráfico es excesivamente complejo con más de 2500 líneas de código, múltiples componentes innecesarios, y funcionalidades que no aportan valor real. Se requiere una simplificación radical que mantenga únicamente dos funcionalidades esenciales: modificar la configuración del sistema y controlar los servicios. El objetivo es reducir la complejidad de código de ~2500 líneas a menos de 500 líneas totales, eliminando toda la sobre-ingeniería y enfocándose en funcionalidad práctica y simplicidad.

## Requirements

### Requirement 1: Gestión Simplificada de Configuración

**User Story:** Como desarrollador del sistema de tráfico, quiero poder modificar los ajustes del config.yaml de forma visual y simple, para evitar editar manualmente el archivo YAML y reducir errores de configuración.

#### Acceptance Criteria

1. WHEN accedo a la página de configuración THEN el sistema SHALL mostrar todos los campos del config.yaml actual en formularios editables
2. WHEN modifico un valor de configuración THEN el sistema SHALL validar básicamente el tipo de dato (int, float, str, bool)
3. WHEN hago clic en "Guardar" THEN el sistema SHALL escribir los cambios al archivo config.yaml y mostrar confirmación de éxito
4. WHEN hago clic en "Cancelar" THEN el sistema SHALL descartar todos los cambios no guardados y revertir a los valores originales
5. WHEN hago clic en "Recargar" THEN el sistema SHALL leer nuevamente el config.yaml desde disco y actualizar la interfaz
6. IF hay errores de validación THEN el sistema SHALL mostrar mensajes de error claros sin permitir guardar
7. WHEN guardo exitosamente THEN el sistema SHALL mostrar un mensaje de confirmación "✅ Configuración guardada"

### Requirement 2: Control Simplificado de Servicios

**User Story:** Como desarrollador del sistema de tráfico, quiero poder iniciar y detener los servicios del sistema desde una interfaz web, para evitar usar múltiples terminales y comandos manuales.

#### Acceptance Criteria

1. WHEN accedo a la página de servicios THEN el sistema SHALL mostrar una lista de los 4 servicios principales (simulation, decision, detection, reporting)
2. WHEN veo la lista de servicios THEN el sistema SHALL mostrar el estado actual de cada servicio (🟢 Activo / 🔴 Inactivo)
3. WHEN hago clic en "Iniciar" para un servicio inactivo THEN el sistema SHALL ejecutar el archivo run_*.py correspondiente y actualizar el estado
4. WHEN hago clic en "Detener" para un servicio activo THEN el sistema SHALL terminar el proceso del servicio y actualizar el estado
5. WHEN hago clic en "Iniciar Todos" THEN el sistema SHALL iniciar todos los servicios inactivos secuencialmente
6. WHEN hago clic en "Detener Todos" THEN el sistema SHALL detener todos los servicios activos
7. IF un servicio falla al iniciar THEN el sistema SHALL mostrar un mensaje de error específico
8. WHEN una operación de servicio es exitosa THEN el sistema SHALL mostrar confirmación "✅ Servicio iniciado/detenido"

### Requirement 3: Navegación Minimalista

**User Story:** Como usuario del frontend, quiero una navegación simple entre las dos páginas principales, para acceder rápidamente a las funcionalidades sin distracciones.

#### Acceptance Criteria

1. WHEN accedo al frontend THEN el sistema SHALL mostrar una navegación con exactamente 2 opciones: "⚙️ Configuración" y "🔧 Servicios"
2. WHEN hago clic en una opción de navegación THEN el sistema SHALL cambiar a esa página inmediatamente
3. WHEN estoy en una página THEN el sistema SHALL indicar visualmente cuál página está activa
4. WHEN inicio el frontend THEN el sistema SHALL abrir por defecto en la página de servicios

### Requirement 4: Arquitectura Simplificada

**User Story:** Como desarrollador manteniendo el código, quiero una estructura de archivos simple y clara, para facilitar el mantenimiento y evitar complejidad innecesaria.

#### Acceptance Criteria

1. WHEN reviso la estructura del frontend THEN el sistema SHALL tener máximo 4 archivos principales
2. WHEN reviso el código total THEN el sistema SHALL tener menos de 500 líneas de código en total
3. WHEN reviso las dependencias THEN el sistema SHALL usar únicamente Streamlit, PyYAML, subprocess y psutil
4. WHEN reviso la funcionalidad THEN el sistema SHALL NO incluir: dashboards, logs, métricas, health checks, troubleshooting, auto-refresh complejo, validaciones avanzadas con Pydantic
5. IF necesito agregar funcionalidad THEN el sistema SHALL mantener el principio de simplicidad sobre características adicionales

### Requirement 5: Validación Básica y Manejo de Errores

**User Story:** Como usuario del frontend, quiero que el sistema valide mis entradas y maneje errores de forma clara, para evitar configuraciones incorrectas y problemas de servicios.

#### Acceptance Criteria

1. WHEN ingreso un valor inválido en configuración THEN el sistema SHALL mostrar un mensaje de error claro junto al campo
2. WHEN intento guardar configuración con errores THEN el sistema SHALL prevenir el guardado y resaltar los campos problemáticos
3. WHEN un servicio falla al iniciar THEN el sistema SHALL mostrar el mensaje de error específico del proceso
4. WHEN hay un error de lectura/escritura de config.yaml THEN el sistema SHALL mostrar un mensaje de error descriptivo
5. IF ocurre un error inesperado THEN el sistema SHALL mostrar un mensaje genérico sin crashear la aplicación
