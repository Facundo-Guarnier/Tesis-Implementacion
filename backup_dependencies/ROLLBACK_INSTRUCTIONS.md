# 🔄 INSTRUCCIONES DE ROLLBACK COMPLETO

## ⚠️ SI ALGO SALE MAL, EJECUTA ESTOS PASOS:

### PASO 1: Revertir archivos de configuración
```bash
copy pyproject.toml.backup pyproject.toml
copy poetry.lock.backup poetry.lock
```

### PASO 2: Eliminar entorno virtual actual
```bash
poetry env remove --all
```

### PASO 3: Recrear entorno con Python 3.11.9
```bash
# Asegúrate de estar usando Python 3.11.9
python --version  # Debe mostrar 3.11.9

# Recrear entorno
poetry install
```

### PASO 4: Verificar funcionamiento
```bash
python run_decision_agent.py  # Debe mostrar el error original
python test_sumo_smoke.py     # SUMO debe funcionar
```

## 📋 Estado original guardado:
- **Python**: 3.11.9
- **TensorFlow**: 2.14.0
- **Entorno**: traffic-system-0IpZKoqG-py3.11
- **Dependencias**: backup_dependencies_actual.txt
- **Config Python**: backup_python_config.json

## 🆘 En caso de emergencia total:
1. Desinstalar Python 3.12+
2. Reinstalar Python 3.11.9 desde Microsoft Store
3. Ejecutar los pasos 1-4 arriba

**FECHA BACKUP:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
