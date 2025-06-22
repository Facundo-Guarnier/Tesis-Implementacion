# 📦 Dependencias del Proyecto

Este documento lista las librerías y paquetes de sistema requeridos para ejecutar el proyecto.

## 🐍 Librerías de Python (pip)

Instala los siguientes paquetes usando `pip`:

```bash
pip install Flask
pip install mypy
pip install types-PyYAML
pip install cvzone
pip install --upgrade opencv-python
pip install ultralytics
pip install traci
pip install supervision
pip install pydantic
```

> 📝 Nota: Se recomienda encarecidamente utilizar un entorno virtual (venv) para gestionar estas dependencias.

## 🐧 Paquetes del Sistema (para Ubuntu/Debian)

Se requiere SUMO para la simulación de tráfico. Instálalo usando apt:

```bash
sudo add-apt-repository ppa:sumo/stable -y
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-doc
```
