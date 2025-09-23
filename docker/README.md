# 🐳 Docker - Servicios Decision y Reporting

Dockerfiles simples para ejecutar los servicios Decision Agent (DQN) y Reporting Service.

## 📦 Estructura

```
docker/
├── decision-agent/Dockerfile    # Servicio DQN
├── reporting-service/Dockerfile # Servicio de Reportes
└── README.md
```

## 🚀 Uso

### Construir imágenes

```bash
# Decision Agent
docker build -f docker/decision-agent/Dockerfile -t traffic-decision-agent .

# Reporting Service
docker build -f docker/reporting-service/Dockerfile -t traffic-reporting-service .
```

### Ejecutar servicios

```bash
# Decision Agent (pasar IP como parámetro)
docker run -d --name decision-agent \
  -v ./assets/dqn_models:/app/assets/dqn_models:ro \
  -v ./logs/services:/app/logs/services \
  -v ./config.yaml:/app/config.yaml:ro \
  traffic-decision-agent

# Reporting Service (pasar IP como parámetro)
docker run -d --name reporting-service \
  -v ./results/reportes:/app/results/reportes \
  -v ./logs/services:/app/logs/services \
  -v ./config.yaml:/app/config.yaml:ro \
  traffic-reporting-service
```

### Ver logs

```bash
docker logs -f decision-agent
docker logs -f reporting-service
```

### Detener servicios

```bash
docker stop decision-agent reporting-service
docker rm decision-agent reporting-service
```

## ⚙️ Configuración

- **IP de APIs**: Se pasa como parámetro al ejecutar el contenedor
- **Modelos DQN**: Montar `assets/dqn_models/` como volumen
- **Reportes**: Montar `results/reportes/` como volumen
- **Logs**: Montar `logs/services/` como volumen
- **Config**: Montar `config.yaml` como volumen

## 📝 Notas

- Los servicios son **clientes** que consumen APIs externas
- No exponen puertos (solo consumen)
- Requieren que Simulation/Detection estén ejecutándose en tu PC
- La IP se configura al momento de ejecutar, no en variables de entorno
