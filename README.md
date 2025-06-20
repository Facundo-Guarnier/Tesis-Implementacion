<p align="center">
    <img src="./docs/assets/um_emblem.png" alt="Universidad de Mendoza: Ingeniería" width="180"/>
</p>

# Trabajo Final Integrador de Grado

## INGENIERÍA EN INFORMÁTICA

## Facundo Guarnier

### Sistema de Semáforos Inteligentes

**2024 - Mendoza, Argentina**

**Asesor Especialista: Ignacio Bosch**

## Resumen

Este repositorio contiene el Trabajo Final de Grado "Sistema de semáforos inteligentes", que aborda la congestión vehicular en las intersecciones de la calle Rondeau/Arenales con el Acceso Este en Guaymallén, Mendoza. El proyecto propone un sistema de semáforos inteligentes para optimizar el flujo de tráfico, reducir tiempos de espera y mejorar la eficiencia vehicular.

El sistema se basa en una arquitectura que integra la detección de vehículos con YOLOv8, la simulación de tráfico con SUMO, y la toma de decisiones mediante una red neuronal Deep Q-Network (DQN) entrenada en un entorno de simulación. Los resultados demuestran que el sistema supera a los semáforos de tiempo fijo, logrando una mayor fluidez del tráfico y reducción de demoras, tanto en condiciones normales como de alto volumen vehicular.

## Tecnologías utilizadas

- **Python**: Lenguaje principal del proyecto.
- **YOLOv8**: Modelo de detección de objetos para identificar vehículos en video.
- **SUMO**: Simulador de tráfico para modelar y evaluar el sistema de semáforos.
- **TensorFlow**: Framework de aprendizaje profundo utilizado para entrenar la red neuronal DQN.
- **Deep Q-Network (DQN)**: Algoritmo de aprendizaje por refuerzo para la toma de decisiones en tiempo real.
- **OpenCV**: Biblioteca para procesamiento de imágenes y video.
- **Git**: Control de versiones para gestionar el código fuente.
- **Visual Studio Code**: Entorno de desarrollo integrado (IDE) utilizado para el desarrollo del proyecto.
- **Pre-commit hooks**: Herramientas para mantener la calidad del código mediante linters y formateadores automáticos.
