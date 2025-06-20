# ⚙️ Configuración de Visual Studio Code

Para asegurar un estilo de código consistente y aprovechar las herramientas de calidad, se recomienda la siguiente configuración en Visual Studio Code para este proyecto.

## 🧩 Extensiones Recomendadas

Instala las siguientes extensiones desde el Marketplace de VS Code para activar el formateo, linting y chequeo de tipos automáticos.

- **Python** (`ms-python.python`): Extensión fundamental para el desarrollo con Python.
- **Black Formatter** (`ms-python.black-formatter`): Formateador de código que se activa automáticamente al guardar.
- **isort** (`ms-python.isort`): Organiza los `import` de manera automática y consistente.
- **Ruff** (`charliermarsh.ruff`): Linter y auto-corrector de código extremadamente rápido.
- **Mypy Type Checker** (`ms-python.mypy-type-checker`): Verificador de tipos estáticos para detectar errores antes de la ejecución.
- **Code Spell Checker** (`streetsidesoftware.code-spell-checker`): Ayuda a detectar errores ortográficos en el código.

## 📁 Archivo de Configuración (`.vscode/settings.json`)

Este archivo activa y configura las extensiones mencionadas para que funcionen automáticamente al guardar los archivos Python.

### Pasos para Aplicar la Configuración

1.  Crea una carpeta llamada `.vscode` en la raíz de tu proyecto (si no existe).
2.  Dentro de la carpeta `.vscode`, crea un archivo llamado `settings.json`.
3.  Copia y pega el siguiente contenido en el archivo `settings.json`:

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
  "isort.args": ["--profile", "black"],
  "ruff.enable": true,
  "ruff.fixAll": true,
  "mypy.enabled": true,
  "mypy.runUsingActiveInterpreter": true
}
```

4.  Reinicia VS Code para asegurarte de que todas las configuraciones se apliquen correctamente.

## 🛡️ Configuración de Pre-commit

Para asegurar que el código cumple con los estándares de calidad antes de cada commit, se utiliza un hook de pre-commit. Esto garantiza que las herramientas de formateo y chequeo se ejecuten automáticamente.

```bash
git config core.hooksPath .githooks
```

### 🚀 Ejecutar Pre-commit manualmente:Ejecutar Pre-commit manualmente:

**Windows PowerShell:**

```powershell
powershell -ExecutionPolicy Bypass -File .githooks/pre-commit.ps1
```

**Linux/macOS/WSL:**

```bash
bash .githooks/pre-commit
```
