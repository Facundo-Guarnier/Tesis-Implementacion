# Implementation Plan

- [x] 1. Crear estructura base del frontend simplificado


  - Crear el archivo principal app.py con navegación básica entre 2 páginas
  - Implementar inicialización de sesión y configuración básica de Streamlit
  - Configurar logging básico con emojis para errores y advertencias
  - _Requirements: 3.1, 3.2, 3.3, 4.1_

- [ ] 2. Implementar gestor de configuración con validación Pydantic
  - [x] 2.1 Crear ConfigManager con carga y guardado de config.yaml


    - Implementar método load_config() para leer config.yaml preservando estructura
    - Implementar método save_config() con escritura segura del archivo YAML
    - Agregar manejo de errores básico para archivos corruptos o faltantes
    - _Requirements: 1.1, 1.5, 5.4_

  - [x] 2.2 Integrar validación completa con AppSettings de Pydantic


    - Implementar validate_with_pydantic() usando el modelo existente AppSettings
    - Crear función para validación de campos individuales en tiempo real
    - Implementar extracción de mensajes de error específicos de ValidationError
    - _Requirements: 1.2, 5.1, 5.2_

  - [x] 2.3 Implementar sistema de ayuda contextual desde comentarios YAML


    - Crear parser para extraer comentarios del config.yaml original
    - Implementar get_field_help() para mostrar ayuda por campo
    - Mapear comentarios a rutas de campos específicos (ej: 'services.simulation_port')
    - _Requirements: 1.1, 5.1_

- [ ] 3. Crear página de configuración con formularios validados
  - [x] 3.1 Implementar renderizado de secciones de configuración


    - Crear render_config_page() con estructura de secciones (Servicios, Detección, etc.)
    - Implementar widgets apropiados por tipo de dato (checkbox, number_input, text_input)
    - Agregar indicadores visuales de validación (✅❌⚠️) junto a cada campo
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 3.2 Implementar controles de guardado y cancelación

    - Crear botones Guardar/Cancelar/Recargar con estados apropiados
    - Implementar lógica de guardado con validación previa completa
    - Agregar confirmación de éxito y manejo de errores de guardado
    - _Requirements: 1.3, 1.4, 1.5_

  - [x] 3.3 Agregar validación en tiempo real por campo

    - Implementar validación inmediata al cambiar valores en formularios
    - Mostrar mensajes de error específicos junto a campos inválidos
    - Prevenir guardado cuando hay errores de validación pendientes
    - _Requirements: 1.2, 5.1, 5.2_

- [ ] 4. Implementar controlador de servicios
  - [x] 4.1 Crear ServiceController para gestión de procesos


    - Implementar get_service_status() usando psutil para verificar procesos activos
    - Crear mapeo de servicios a archivos run_*.py correspondientes
    - Implementar detección de procesos por nombre y comando ejecutado
    - _Requirements: 2.2, 2.7_

  - [x] 4.2 Implementar inicio y parada de servicios individuales


    - Crear start_service() usando subprocess para ejecutar run_*.py con poetry
    - Implementar stop_service() usando psutil para terminar procesos específicos
    - Agregar manejo de errores para servicios que fallan al iniciar/detener
    - _Requirements: 2.3, 2.4, 2.7, 2.8_

  - [x] 4.3 Agregar operaciones masivas de servicios


    - Implementar start_all_services() para iniciar todos los servicios secuencialmente
    - Crear stop_all_services() para detener todos los servicios activos
    - Agregar logging de operaciones exitosas y fallidas
    - _Requirements: 2.5, 2.6, 2.8_

- [ ] 5. Crear página de control de servicios
  - [x] 5.1 Implementar interfaz de estado de servicios


    - Crear render_services_page() con lista de 4 servicios principales
    - Mostrar estado visual de cada servicio (🟢 Activo / 🔴 Inactivo)
    - Implementar actualización de estado en tiempo real al hacer cambios
    - _Requirements: 2.1, 2.2_

  - [x] 5.2 Agregar controles individuales por servicio

    - Crear botones Iniciar/Detener por cada servicio con estados apropiados
    - Implementar feedback inmediato de operaciones (éxito/error)
    - Mostrar mensajes de error específicos cuando servicios fallan
    - _Requirements: 2.3, 2.4, 2.7, 2.8_

  - [x] 5.3 Implementar controles masivos

    - Agregar botones "Iniciar Todos" y "Detener Todos"
    - Mostrar progreso de operaciones masivas con feedback por servicio
    - Implementar manejo de errores parciales (algunos servicios fallan)
    - _Requirements: 2.5, 2.6, 2.8_

- [x] 6. Crear utilidades básicas y logging

  - Implementar utils.py con funciones de logging estratégico
  - Crear setup_logging() para configuración básica de logs
  - Implementar log_error(), log_warning(), log_success() con emojis apropiados
  - Agregar funciones auxiliares para manejo de rutas y validaciones básicas
  - _Requirements: 4.3, 5.5_

- [ ] 7. Integrar navegación y flujo completo
  - [x] 7.1 Implementar navegación entre páginas

    - Crear render_navigation() con exactamente 2 opciones de menú
    - Implementar indicación visual de página activa
    - Configurar página de servicios como página por defecto
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 7.2 Conectar todos los componentes en app.py principal

    - Integrar ConfigManager y ServiceController en la aplicación principal
    - Implementar inicialización de estado de sesión para ambas páginas
    - Agregar manejo global de errores y logging de aplicación
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 8. Realizar limpieza y eliminación de código legacy


  - Eliminar completamente los archivos de componentes complejos existentes
  - Remover utils/validation_utils.py y utils/validators.py redundantes
  - Limpiar imports no utilizados y dependencias innecesarias
  - Verificar que el código total sea menor a 500 líneas
  - _Requirements: 4.1, 4.2, 4.4_

- [ ] 9. Realizar testing básico de funcionalidades


  - Verificar carga correcta de config.yaml con validación Pydantic
  - Probar modificación y guardado de configuración con diferentes tipos de datos
  - Verificar inicio y parada de servicios individuales y masivos
  - Confirmar navegación entre páginas y estado de sesión
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.3, 2.4, 3.1_
