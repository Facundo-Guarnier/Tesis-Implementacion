# ⚙️ Configuración de Visual Studio Code

Para asegurar un estilo de código consistente y aprovechar las herramientas de calidad, se recomienda la siguiente configuración en Visual Studio Code para este proyecto.

## 🧩 Extensiones Recomendadas

Instala las siguientes extensiones desde el Marketplace de VS Code para activar el formateo, linting y chequeo de tipos automáticos.

- **Python** (`ms-python.python`): Extensión fundamental para el desarrollo con Python.
- **Black Formatter** (`ms-python.black-formatter`): Formateador de código que se activa automáticamente al guardar.
- **Mypy Type Checker** (`ms-python.mypy-type-checker`): Verificador de tipos estáticos para detectar errores antes de la ejecución.
- **Code Spell Checker** (`streetsidesoftware.code-spell-checker`): Ayuda a detectar errores ortográficos en el código.

## 📁 Archivo de Configuración (`.vscode/settings.json`)

Este archivo activa y configura las extensiones mencionadas para que funcionen automáticamente al guardar los archivos Python con **Poetry** como gestor de entorno.

### Pasos para Aplicar la Configuración

1. Crea una carpeta llamada `.vscode` en la raíz de tu proyecto (si no existe).
2. Dentro de la carpeta `.vscode`, crea un archivo llamado `settings.json`.
3. Copia y pega el siguiente contenido en el archivo `settings.json`:

```json
{
  "cSpell.words": ["palabras"],
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll.ruff": "explicit"
    },
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "ruff.enable": true,
  "ruff.fixAll": true,
  "mypy-type-checker.preferDaemon": true,
  "mypy-type-checker.reportingScope": "workspace",
  "mypy-type-checker.importStrategy": "fromEnvironment"
}
```

4. **Seleccionar intérprete de Poetry**: `Ctrl+Shift+P` → "Python: Select Interpreter" → Elegir el entorno virtual de Poetry
5. Reinicia VS Code para asegurarte de que todas las configuraciones se apliquen correctamente.

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
