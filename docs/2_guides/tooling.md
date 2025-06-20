# 🛠️ Herramientas de automatización

Este proyecto utiliza herramientas automáticas para mantener la calidad, legibilidad y consistencia del código fuente.

---

### 📦 Herramientas activas

| Herramienta                               | Propósito                                | Cuándo se ejecuta          |
| ----------------------------------------- | ---------------------------------------- | -------------------------- |
| [`isort`](https://pycqa.github.io/isort/) | Organiza y agrupa los imports            | ✅ Al guardar + Pre-commit |
| [`Ruff`](https://docs.astral.sh/ruff/)    | Linter rápido + correcciones automáticas | ✅ Al guardar + Pre-commit |
| [`Black`](https://black.readthedocs.io/)  | Formato automático de código             | ✅ Al guardar + Pre-commit |
| [`Mypy`](http://mypy-lang.org/)           | Verificación de tipos estáticos          | ❌ Solo en pre-commit      |

---

### 🔄 Orden de ejecución

**💾 Al guardar archivos en VSCode:**

1. isort → Organiza los imports
2. Ruff → Aplica correcciones rápidas
3. Black → Da formato uniforme al código

**⛔ Antes de cada commit (pre-commit hook):**

1. isort → Reordena los imports
2. Ruff → Linting + autofixes
3. Black → Formateo final
4. Mypy → Verificación de tipos

> 💡 **Importante**: Si el hook de pre-commit encuentra errores o modifica archivos, el commit se cancela automáticamente. Los archivos modificados se añaden al staging area, y debes hacer commit nuevamente con el código ya limpio.

---

### ⚙️ Automatización

- **VSCode**: Ejecuta `isort`, `ruff` y `black` automáticamente al guardar archivos `.py`.
- **Git (pre-commit)**: Ejecuta todas las herramientas antes de confirmar cambios.
- **Manual**: Puedes ejecutar el script `.githooks/pre-commit.ps1` para verificar todo el proyecto.

---

## 🎨 Configuración detallada

### **Black**

- Longitud máxima de línea: `88` caracteres
- Añade comas finales en listas/diccionarios multilínea
- No requiere configuración extra

### **isort**

- Perfil: `black` (compatibilidad total)
- Orden: Librerías estándar → Terceros → Módulos locales
- Añade una línea en blanco entre secciones

### **Ruff**

- Mucho más rápido que `flake8` o `pylint`
- Elimina imports no usados, variables innecesarias, etc.
- Sustituye: `flake8`, `pylint` y parcialmente `isort`

### **Mypy**

- Ignora imports que no puede analizar (`ignore_missing_imports = True`)
- Verificación de tipos solo en pre-commit
- Puede extenderse a más archivos progresivamente

---

## 🚀 Instalación y configuración

### Para nuevos desarrolladores

1. Instalar las herramientas de desarrollo:

```bash
pip install -r requirements-dev.txt
```

2. Configurar el hook de pre-commit:

```bash
git config core.hooksPath .githooks
```

3. Instalar las extensiones recomendadas en VSCode:

- Black Formatter (ms-python.black-formatter)
- isort (ms-python.isort)
- Ruff (charliermarsh.ruff)
- Mypy Type Checker (ms-python.mypy-type-checker)

## 🤚🏻 Verificación manual

```bash
# Ejecutar todas las herramientas como pre-commit
powershell -ExecutionPolicy Bypass -File .githooks/pre-commit.ps1

# O ejecutar herramientas individuales
python3 -m black .
python3 -m isort .
python3 -m ruff check --fix .
python3 -m mypy --config-file=mypy.ini .
```

> 📝 Nota: Esta configuración ayuda a mantener un estilo coherente, detectar errores comunes y asegurar la calidad del código de forma automática.
