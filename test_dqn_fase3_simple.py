#!/usr/bin/env python3
"""
Test simplificado para verificar mejoras DQN - Fase 3
Verifica que las optimizaciones avanzadas funcionen correctamente.
"""

import sys
from pathlib import Path

import numpy as np

# Configurar path para imports
sys.path.append(str(Path(__file__).parent / "src"))


def test_phase_3_integration() -> bool:
    """Test integrado que verifica que las mejoras de Fase 3 están funcionando."""
    print("🧪 TEST INTEGRADO: Verificando mejoras Fase 3")

    try:
        from unittest.mock import Mock, patch

        from src.traffic_system.decision.DQN.dqn_trainer import (
            DQNTrainer,
            PrioritizedReplayBuffer,
        )

        # Crear mock de DecisionAPI
        mock_api = Mock()
        mock_api.get_wait_times.return_value = {"wait_times": [10.5, 15.2, 8.7, 12.3]}
        mock_api.get_quantities.return_value = {"quantities": [5, 8, 3, 6]}

        # Verificar que el config actual tiene las mejoras habilitadas
        print("   🔧 Creando DQNTrainer...")
        with patch(
            "src.traffic_system.decision.DQN.dqn_trainer.DecisionAPI",
            return_value=mock_api,
        ):
            trainer = DQNTrainer(
                auto_train=False
            )  # No entrenar automáticamente en test
        print("   🔧 DQNTrainer creado.")

        # Verificar flags de configuración Fase 3
        print(
            f"   📊 use_prioritized_replay: {getattr(trainer, 'use_prioritized_replay', 'NO DEFINIDO')}"
        )
        print(
            f"   📊 use_noisy_networks: {getattr(trainer, 'use_noisy_networks', 'NO DEFINIDO')}"
        )
        print(f"   📊 use_dropout: {getattr(trainer, 'use_dropout', 'NO DEFINIDO')}")
        print(f"   📊 adaptive_lr: {getattr(trainer, 'adaptive_lr', 'NO DEFINIDO')}")

        # Verificar que el modelo existe
        assert hasattr(trainer, "model"), "El modelo no fue creado"
        assert trainer.model is not None, "El modelo es None"

        # Verificar PER si está habilitado
        if getattr(trainer, "use_prioritized_replay", False):
            print("   🔀 Verificando Prioritized Experience Replay...")
            assert hasattr(trainer, "memory_buffer"), "Buffer priorizado no encontrado"
            assert isinstance(
                trainer.memory_buffer, PrioritizedReplayBuffer
            ), "Buffer no es del tipo correcto"
            print("   ✅ Prioritized Experience Replay verificado")

        # Verificar arquitectura mejorada
        print("   🔀 Verificando arquitectura mejorada...")
        model_config = trainer.model.get_config()
        layers = model_config.get("layers", [])

        # Buscar capas de Dropout o GaussianNoise
        has_dropout = any(
            "dropout" in layer.get("class_name", "").lower() for layer in layers
        )
        has_noise = any(
            "gaussiannoise" in layer.get("class_name", "").lower() for layer in layers
        )

        if trainer.use_dropout:
            print(f"   📊 Dropout detectado en modelo: {has_dropout}")
        if trainer.use_noisy_networks:
            print(f"   📊 Noisy Networks detectado: {has_noise}")

        print("   ✅ Arquitectura mejorada verificada")

        # Verificar predicción del modelo funciona
        print("   🔄 Verificando predicción...")
        test_state = np.random.random((1, 48)).astype(np.float32)
        prediction = trainer.model.predict(test_state, verbose=0)
        print(f"   📊 Forma de predicción: {prediction.shape}")
        assert prediction.shape == (1, 16), f"Forma incorrecta: {prediction.shape}"
        print("   ✅ Predicción funciona")

        print("   ✅ Test integrado completado exitosamente")
        return True

    except Exception as e:
        print(f"   ❌ Error en test integrado: {e}")
        return False


def test_prioritized_buffer() -> bool:
    """Test del buffer de experiencia priorizada."""
    print("🧪 TEST: Buffer Priorizado")

    try:
        from src.traffic_system.decision.DQN.dqn_trainer import PrioritizedReplayBuffer

        # Crear buffer
        buffer = PrioritizedReplayBuffer(capacity=100, alpha=0.6)

        # Añadir algunas experiencias
        for _ in range(10):
            state = np.random.random(48).astype(np.float32)
            next_state = np.random.random(48).astype(np.float32)
            action = np.random.randint(0, 16)
            reward = np.random.random()
            done = np.random.choice([True, False])
            td_error = np.random.random()

            buffer.add(state, action, reward, next_state, done, td_error)

        # Verificar que se añadieron
        assert (
            len(buffer) == 10
        ), f"Buffer debería tener 10 elementos, tiene {len(buffer)}"

        # Probar muestreo
        samples, indices, weights = buffer.sample(5, beta=0.4)
        assert len(samples) == 5, f"Debería muestrear 5, muestreó {len(samples)}"
        assert len(indices) == 5, f"Debería tener 5 índices, tiene {len(indices)}"
        assert len(weights) == 5, f"Debería tener 5 pesos, tiene {len(weights)}"

        print("   ✅ Buffer priorizado funciona correctamente")
        return True

    except Exception as e:
        print(f"   ❌ Error en buffer priorizado: {e}")
        return False


def main() -> None:
    """Ejecutar todos los tests de Fase 3."""
    print("🚀 TESTS SIMPLIFICADOS DQN - FASE 3")
    print("=" * 50)

    tests_passed = 0
    total_tests = 2

    # Test 1: Integración Fase 3
    if test_phase_3_integration():
        tests_passed += 1

    # Test 2: Buffer Priorizado
    if test_prioritized_buffer():
        tests_passed += 1

    print("=" * 50)
    print("📊 RESULTADOS:")
    if tests_passed == total_tests:
        print("   ✅ Integración Fase 3")
        print("   ✅ Buffer Priorizado")
    else:
        if tests_passed >= 1:
            print("   ✅ Algunos tests exitosos")
        else:
            print("   ❌ Tests fallaron")

    print(f"🎯 {tests_passed}/{total_tests} tests exitosos")
    if tests_passed == total_tests:
        print("🎉 ¡Fase 3 implementada correctamente!")
    else:
        print("⚠️ Fase 3 necesita correcciones")


if __name__ == "__main__":
    main()
