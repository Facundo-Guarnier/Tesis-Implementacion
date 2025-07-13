# ⚙️ Configuración de VSCode para Formateo Automático

Esta guía asegura que VSCode aplique automáticamente el mismo formateo que pre-commit, eliminando discrepancias entre el guardado en el editor y las verificaciones automáticas.

## 🧩 Extensiones Requeridas

El archivo `.vscode/extensions.json` especifica automáticamente las extensiones necesarias:

- **Python** (`ms-python.python`): Soporte básico de Python
- **Black Formatter** (`ms-python.black-formatter`): Formateo automático de código
- **Ruff** (`charliermarsh.ruff`): Linting e import sorting (reemplaza isort)
- **Mypy Type Checker** (`ms-python.mypy-type-checker`): Verificación de tipos estáticos

## ⚙️ Configuración Automática (`.vscode/settings.json`)

La configuración actual aplica automáticamente.

### 🔄 Flujo Automático al Guardar (Ctrl+S)

1. **Ruff**: Organiza imports + aplica correcciones automáticas
2. **Black**: Formatea código con 88 caracteres por línea
3. **MyPy**: Verifica tipos en background

## 🧪 Verificación

### 1. Instalar extensiones recomendadas:

- VSCode mostrará automáticamente una notificación
- O ejecutar: `Ctrl+Shift+P` → "Extensions: Show Recommended Extensions"

### 2. Seleccionar intérprete de Poetry:

- `Ctrl+Shift+P` → "Python: Select Interpreter"
- Elegir el entorno de Poetry (termina en `traffic-system-xxx`)

## 🛡️ Configuración de Pre-commit

Para asegurar que el código cumple con los estándares de calidad antes de cada commit, se utiliza **pre-commit framework** con Poetry:

```bash
# Instalar hooks (solo primera vez)
poetry run pre-commit install
```

### 🚀 Ejecutar Pre-commit manualmente:

```bash
# Ejecutar en todo el proyecto
poetry run pre-commit run --all-files

# Ejecutar en archivos específicos
poetry run pre-commit run --files src/archivo.py
```

## 🚨 Solución de Problemas

### Pre-commit encuentra errores después de guardar:

1. **Regenerar configuración**:
   ```bash
   poetry run pre-commit clean
   poetry run pre-commit install --install-hooks
   ```

## ✅ Resultado

Con esta configuración:

- ✅ **Formateo consistente**: VSCode aplica exactamente las mismas reglas que pre-commit
- ✅ **Imports organizados**: Ruff los ordena automáticamente al guardar
- ✅ **Flujo eficiente**: Sin errores de pre-commit después de guardar
- ✅ **Type checking**: MyPy verifica tipos en tiempo real
