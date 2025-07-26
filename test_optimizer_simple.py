#!/usr/bin/env python3
"""Test simple para verificar gradient clipping."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.traffic_system.core.config_loader import load_app_settings
from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

# Cargar y crear trainer
config = load_app_settings()
trainer = DQNTrainer(config.decision.entrenamiento)

# Inicializar modelo (normalmente se hace en start_training_process)
trainer.model = trainer._build_model()

# Verificar optimizador
if trainer.model is not None:
    opt = trainer.model.optimizer
    print(f"✅ Optimizer: {type(opt).__name__}")
    print(f"✅ Clipnorm: {getattr(opt, 'clipnorm', 'No configurado')}")
    print(f"✅ Clipvalue: {getattr(opt, 'clipvalue', 'No configurado')}")
    print(f"✅ Learning rate: {opt.learning_rate}")

    print("\n🎯 Configuración corregida:")
    print("- Solo clipnorm=1.0 (sin clipvalue)")
    print("- Esto debería funcionar en Linux con GPU")

    # Verificar que no hay conflicto de parámetros
    has_clipnorm = hasattr(opt, "clipnorm") and opt.clipnorm is not None
    has_clipvalue = hasattr(opt, "clipvalue") and opt.clipvalue is not None

    if has_clipnorm and not has_clipvalue:
        print("✅ Configuración CORRECTA: Solo clipnorm configurado")
    elif has_clipnorm and has_clipvalue:
        print("❌ ERROR: Ambos clipnorm Y clipvalue configurados")
    else:
        print("⚠️ Advertencia: Ningún gradient clipping configurado")
else:
    print("❌ Error: Modelo no inicializado")
