# Instrucciones y Prompts para IA

Esta carpeta contiene instrucciones específicas y prompts reutilizables para agentes de IA que trabajan en el proyecto.

## 📁 Estructura

```
.github/
├── copilot-instructions.md     # Instrucciones principales
├── instructions/               # Instrucciones específicas por tipo de archivo
│   ├── python-development.instructions.md
│   ├── config-files.instructions.md
│   └── testing.instructions.md
└── prompts/                   # Prompts reutilizables para tareas comunes
    ├── create-api-endpoint.prompt.md
    ├── add-configuration.prompt.md
    └── debug-system.prompt.md
```

## 🎯 Cómo Usar

### Instrucciones Automáticas

Las instrucciones en `instructions/` se aplican automáticamente según el tipo de archivo:

- `python-development.instructions.md`: Para archivos `.py`
- `config-files.instructions.md`: Para archivos de configuración
- `testing.instructions.md`: Para archivos `test_*.py`

### Prompts Manuales

Los prompts en `prompts/` se ejecutan manualmente:

- En VS Code: Escribir `/nombre-del-prompt` en el chat
- Desde Command Palette: `Chat: Run Prompt`

### Configuración Requerida

Asegúrate de tener en `.vscode/settings.json`:

```json
{
  "github.copilot.chat.codeGeneration.useInstructionFiles": true,
  "chat.instructionsFilesLocations": [".github/instructions"],
  "chat.promptFilesLocations": [".github/prompts"]
}
```

## 📚 Documentación Adicional

- [Quick Start Guide](QUICK_START.md)
- [API Reference](API_REFERENCE.md)
- [Testing Guide](TESTING.md)
- [Data Flow Diagram](DATA_FLOW.md)
- [Architecture Decisions](ADR.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## 🔄 Mejores Prácticas

- Las instrucciones son concisas y específicas al proyecto
- Los prompts incluyen contexto completo
- Se referencian archivos y patrones existentes
- Se mantiene consistencia con las convenciones del proyecto
