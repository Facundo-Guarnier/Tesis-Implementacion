# Data Flow

## 🔄 Main Flow
```
📹 Video → 🔍 YOLOv8 → 🧠 DQN → 🚦 SUMO → 📊 Metrics
```

## 📊 Data Pipeline

### 1. Video Input
```
assets/dataset-*/{Zona A-L}/video.mp4
→ Frames (5-30 FPS) → Detection Service
```

### 2. Detection (YOLOv8)
```javascript
Input:  {"frame": "base64", "zones": [...]}
Output: {"detections": [...], "counts": {...}}
```

### 3. Decision (DQN)
```javascript
State:  {"vehicle_counts": [5,3,8,2], "waiting_times": [15.5,10.2,45.8,5.1]}
Action: {"action": "change_phase", "confidence": 0.85}
```

### 4. Control (SUMO)
```javascript
Input:  {"intersection_id": "intersection_1", "new_phase": "green_ew"}
Output: {"success": true, "old_phase": "green_ns"}
```

### 5. Reporting
```javascript
Metrics: {"performance": {...}, "traffic": {...}, "decisions": {...}}
```

## 📁 Key Files

### Config
- `config.yaml` - Main configuration
- `assets/detection_zones/zones.yaml` - Detection zones

### Models
- `assets/yolo_models/yolov8n.pt` - Vehicle detection
- `assets/dqn_models/*.keras` - Traffic light decisions

### Logs
```
logs/services/
├── detection_provider.log
├── decision_agent.log
├── simulation_provider.log
└── reporting_service.log
```

## ⏱️ Frequencies
- **Detection**: 5-30 FPS
- **Decision**: 1-5 seconds
- **Metrics**: 10 seconds
- **Frontend**: 2 seconds

## 💾 States
```python
# Streamlit session
st.session_state = {
  "config": TrafficSystemConfig,
  "service_status": dict,
  "last_metrics": dict
}

# Service cache
{
  "current_detections": dict,
  "decision_history": list,
  "performance_metrics": dict
}
```
