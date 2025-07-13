# 🛠️ Herramientas de Desarrollo y Calidad de Código

Este proyecto utiliza **Poetry** para gestión de dependencias y **pre-commit** para mantener automáticamente la calidad del código.

---

## 📦 Poetry - Gestión de Dependencias

**Poetry** es nuestro gestor de dependencias y entornos virtuales:

```bash
# Activar entorno virtual
poetry shell

# Ejecutar comandos en el entorno
poetry run python run_simulation_provider.py
poetry run pre-commit run --all-files

# Agregar dependencias
poetry add requests            # Producción
poetry add --group dev pytest  # Desarrollo

# Instalar todas las dependencias
poetry install
```

---

## 🔧 Pre-commit - Calidad Automática

**Pre-commit** ejecuta herramientas de calidad automáticamente antes de cada commit:

```bash
# Instalar hooks (solo primera vez)
poetry run pre-commit install

# Ejecutar manualmente
poetry run pre-commit run --all-files

# Ejecutar en archivos específicos
poetry run pre-commit run --files src/traffic_system/core/config_loader.py
```

### 📦 Herramientas integradas en Pre-commit

| Herramienta                              | Propósito                                 | Cuándo se ejecuta        |
| ---------------------------------------- | ----------------------------------------- | ------------------------ |
| [`Ruff`](https://docs.astral.sh/ruff/)   | Linter + Import sorting (reemplaza isort) | ✅ Pre-commit automático |
| [`Black`](https://black.readthedocs.io/) | Formato automático de código              | ✅ Pre-commit automático |
| [`Mypy`](http://mypy-lang.org/)          | Verificación de tipos estáticos           | ✅ Pre-commit automático |

---

### 🔄 Flujo de Pre-commit

**⛔ Antes de cada commit:**

1. **Hooks básicos** → Limpieza de whitespace, EOF, etc.
2. **Ruff** → Linting + Import sorting + autofixes
3. **Black** → Formateo final
4. **Mypy** → Verificación de tipos

> 💡 **Importante**: Si pre-commit encuentra errores o modifica archivos, el commit se cancela automáticamente. Los archivos modificados aparecen como "staged", y debes hacer commit nuevamente con el código ya limpio.

---

### ⚙️ Configuración en VSCode

Para usar estas herramientas en VSCode con Poetry:

1. **Intérprete de Python**: Seleccionar el entorno de Poetry

   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Elegir: `~/.cache/pypoetry/virtualenvs/traffic-system-xxx/bin/python`

2. **Extensiones recomendadas**:
   - Python (Microsoft)
   - Black Formatter
   - isort
   - Ruff

**💾 Al guardar archivos en VSCode:**

1. Ruff → Organiza imports + aplica correcciones rápidas
2. Black → Da formato uniforme al código
3. Mypy → Verifica tipos (en background)

---

## 🎨 Configuración detallada

### **Black**

- Longitud máxima de línea: `88` caracteres
- Configurado en `pyproject.toml`
- Formateo consistente y automático

### **Ruff**

- **Reemplaza completamente a isort** para organización de imports
- Mucho más rápido que `flake8`, `pylint` e `isort`
- Elimina imports no usados, variables innecesarias, etc.
- Configuración de imports en `[tool.ruff.lint.isort]`
- Sustituye: `flake8`, `pylint` e `isort`

### **Mypy**

- Configurado en `mypy.ini`
- Verificación de tipos en todo el proyecto
- Ignora imports que no puede analizar (`ignore_missing_imports = True`)

---

## 🚀 Configuración Inicial para Nuevos Desarrolladores

### 1. Instalar Poetry

**Windows (PowerShell):**

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**Linux/macOS:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Configurar el Proyecto

```bash
# Instalar dependencias
poetry install

# Instalar hooks de pre-commit
poetry run pre-commit install

# Verificar configuración
poetry run pre-commit run --all-files
```

### 3. Configurar VSCode

1. **Seleccionar intérprete de Poetry**:

   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Elegir el entorno virtual de Poetry

2. **Instalar extensiones recomendadas**:
   - Python (Microsoft)
   - Black Formatter
   - Ruff (maneja linting + import sorting)

---

## 🤚🏻 Comandos de Verificación Manual

```bash
# Ejecutar pre-commit en todo el proyecto
poetry run pre-commit run --all-files

# Ejecutar herramientas individuales
poetry run black .
poetry run ruff check --fix .
poetry run mypy .

# Verificar el estado del entorno
poetry env info
poetry show
```

> 📝 **Nota**: Esta configuración automatiza completamente el mantenimiento de la calidad del código, eliminando la necesidad de scripts manuales y asegurando consistencia en todos los commits.
