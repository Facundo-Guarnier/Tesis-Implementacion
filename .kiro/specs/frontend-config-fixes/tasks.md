# Implementation Plan

- [x] 1. Corregir error de encoding UTF-8


  - Modificar ConfigManager.save_config() para usar encoding='utf-8' explícito
  - Agregar parámetros allow_unicode=True y ensure_ascii=False al yaml.dump()
  - Actualizar load_config() para usar encoding='utf-8' en lectura
  - Probar guardado con caracteres Unicode y emojis
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Implementar reactividad del formulario

  - [x] 2.1 Agregar callbacks a widgets de configuración


    - Implementar función on_config_change() como callback universal
    - Agregar parámetro on_change a todos los widgets (number_input, checkbox, text_input)
    - Usar keys únicos para cada widget (formato: config_{field_name})
    - _Requirements: 1.1, 1.2_

  - [x] 2.2 Implementar detección de cambios automática

    - Agregar flag config_modified en session_state
    - Actualizar config_modified=True en callback on_config_change()
    - Habilitar botón "Guardar" cuando config_modified=True
    - _Requirements: 1.2, 1.3_

  - [x] 2.3 Sincronizar estado de validación con cambios


    - Ejecutar validación de campo específico en callback
    - Actualizar validation_errors en session_state por campo
    - Mostrar/ocultar mensajes de error dinámicamente
    - _Requirements: 1.3, 5.1, 5.2_

- [x] 3. Corregir carga de config.yaml

  - [x] 3.1 Mejorar detección de archivos existentes


    - Verificar que config_path use ruta absoluta correcta
    - Mejorar lógica de detección de archivos vacíos vs inexistentes
    - Agregar logging específico para debugging de carga
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 3.2 Implementar configuración por defecto robusta

    - Crear método _create_default_config() con valores válidos
    - Usar configuración por defecto cuando archivo no existe o está vacío
    - Guardar configuración por defecto automáticamente si no existe archivo
    - _Requirements: 3.4, 4.4_

  - [x] 3.3 Corregir inicialización de ConfigManager

    - Cargar configuración inmediatamente en __init__()
    - Almacenar configuración cargada en session_state.current_config
    - Eliminar warning "Archivo de configuración vacío" cuando archivo existe
    - _Requirements: 3.2, 3.3_

- [x] 4. Eliminar logs duplicados

  - [x] 4.1 Implementar inicialización única con session_state


    - Crear flag 'initialized' en session_state para controlar inicialización
    - Mover inicialización de managers a función initialize_session_state()
    - Ejecutar inicialización solo cuando 'initialized' no existe
    - _Requirements: 4.1, 4.2_




  - [-] 4.2 Configurar logging una sola vez por sesión

    - Crear flag 'logging_configured' en session_state


    - Implementar setup_logging_once() que se ejecute solo una vez
    - Evitar re-configuración de handlers en cada re-run de Streamlit
    - _Requirements: 4.1, 4.3_





  - [ ] 4.3 Optimizar mensajes de inicialización
    - Reducir logging de inicialización a mensajes esenciales únicamente
    - Eliminar logs redundantes de verificaciones previas repetidas
    - Usar nivel DEBUG para logs de debugging, INFO solo para eventos importantes


    - _Requirements: 4.3, 4.4_

- [ ] 5. Corregir validación en tiempo real
  - [ ] 5.1 Implementar validación por campo individual
    - Crear función validate_field(field_key, value) para validación específica
    - Usar Pydantic para validar campos individuales contra AppSettings
    - Capturar ValidationError y extraer mensaje específico del campo
    - _Requirements: 5.1, 5.2_

  - [ ] 5.2 Sincronizar validación con estado de botón guardar
    - Deshabilitar botón "Guardar" cuando hay errores en validation_errors
    - Habilitar botón solo cuando config_modified=True y validation_errors está vacío
    - Mostrar contador de errores junto al botón guardar
    - _Requirements: 5.3, 5.4_

  - [ ] 5.3 Mejorar feedback visual de validación
    - Mostrar ✅ junto a campos válidos
    - Mostrar ❌ y mensaje de error junto a campos inválidos
    - Actualizar indicadores inmediatamente al cambiar valores
    - _Requirements: 5.1, 5.2_

- [ ] 6. Testing y verificación de correcciones
  - [ ] 6.1 Probar corrección de encoding
    - Verificar guardado exitoso sin errores de 'charmap'
    - Probar con configuración que genere logs con emojis
    - Verificar que archivo guardado mantiene formato UTF-8
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 6.2 Probar reactividad del formulario
    - Verificar que cambio en campo habilita botón "Guardar" inmediatamente
    - Probar que validación se actualiza en tiempo real
    - Verificar que valores se reflejan correctamente en interfaz
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 6.3 Probar carga de configuración
    - Verificar carga correcta de config.yaml existente
    - Probar creación automática de config por defecto
    - Verificar que no aparece warning de "archivo vacío" incorrectamente
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 6.4 Verificar eliminación de logs duplicados
    - Confirmar que cada mensaje de log aparece solo una vez
    - Verificar que inicialización ocurre solo una vez por sesión
    - Probar que recargas de página no duplican logs innecesariamente
    - _Requirements: 4.1, 4.2, 4.3_
