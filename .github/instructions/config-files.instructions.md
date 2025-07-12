---
description: "Instrucciones para manejar archivos de configuración YAML y modelos Pydantic"
applyTo: "**/config*.{yaml,yml,py}"
---

# Instrucciones para Configuración

## Modificar Configuración

1. **Siempre actualizar `config_models.py` primero** antes de modificar `config.yaml`
2. Definir modelos Pydantic con tipos exactos:

```python
class NuevoSettings(BaseModel):
    campo_requerido: str
    campo_opcional: bool = False
    lista_valores: list[int]
```

3. Añadir al modelo principal `AppSettings`
4. Solo entonces modificar `config.yaml`

## Estructura YAML

- Usar comentarios descriptivos: `#! Campo obligatorio` o `#* Activar funcionalidad`
- Mantener indentación consistente (2 espacios)
- Agrupar configuraciones relacionadas
- Valores por defecto razonables para desarrollo

## Validación

- Pydantic valida automáticamente tipos y campos requeridos
- Errores se muestran en español via `config_loader.py`
- Probar cambios con: `python -c "from src.traffic_system.core.config_loader import load_app_settings; load_app_settings()"`

## Campos Importantes

- `base_url`: URL para comunicación entre servicios
- `path_modelo_entrenado`: Ruta a modelos DQN en `assets/dqn_models/`
- Flags booleanos controlan qué componentes se ejecutan
