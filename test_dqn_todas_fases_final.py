"""
🎯 Test Integrado Final: Todas las Fases DQN (1, 2, 3, 4)

Verifica que todas las mejoras implementadas funcionen correctamente en conjunto.
"""

import os
from unittest.mock import MagicMock, patch

import numpy as np

# Configurar entorno de prueba
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Silenciar logs de TensorFlow


def test_all_phases_integration() -> bool:
    """Test integrado de todas las fases DQN."""
    print("🎯 Iniciando test integrado de todas las fases DQN...")

    with patch("src.traffic_system.decision.DQN.dqn_trainer.DecisionAPI") as mock_api:
        # Configurar mock de la API
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        # Configurar respuestas simuladas consistentes
        mock_api_instance.get_wait_times.return_value = {
            f"zona_{i}": np.random.randint(0, 60) for i in range(1, 13)
        }
        mock_api_instance.get_quantities.return_value = {
            f"zona_{i}": np.random.randint(1, 10) for i in range(1, 13)
        }
        mock_api_instance.advance_simulation.return_value = {"simulation_ended": True}
        mock_api_instance.set_traffic_light_states.return_value = {"success": True}

        # Patch para evitar entrenamiento real
        with patch(
            "src.traffic_system.decision.DQN.dqn_trainer.DQNTrainer._train_agent"
        ):
            from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

            print("📊 Fase 1: Verificando arquitectura base...")
            trainer = DQNTrainer(auto_train=False)

            # Crear modelo manualmente ya que auto_train=False
            if trainer.model is None:
                trainer.model = trainer._build_model()
                trainer.target_model = trainer._build_model()
                trainer.target_model.set_weights(trainer.model.get_weights())
                print("   🏗️ Modelo creado manualmente para testing")

            # Verificar componentes de Fase 1 (Base)
            assert trainer.model is not None
            assert trainer.state_size == 48
            assert trainer.epsilon > 0
            print("   ✅ Fase 1: Arquitectura base funcionando")

            # Verificar componentes de Fase 2 (Mejoras algorítmicas)
            print("📊 Fase 2: Verificando mejoras algorítmicas...")
            assert hasattr(trainer, "use_double_dqn")
            assert trainer.use_double_dqn is True
            assert hasattr(trainer, "target_model")
            assert trainer.target_model is not None
            assert hasattr(trainer, "use_dueling_dqn")
            assert trainer.use_dueling_dqn is True
            print("   ✅ Fase 2: Double DQN y Dueling DQN activos")

            # Verificar componentes de Fase 3 (Optimizaciones avanzadas)
            print("📊 Fase 3: Verificando optimizaciones avanzadas...")
            assert hasattr(trainer, "use_prioritized_replay")
            assert trainer.use_prioritized_replay is True
            assert hasattr(trainer, "memory_buffer")
            assert hasattr(trainer, "use_noisy_networks")
            assert trainer.use_noisy_networks is True
            assert hasattr(trainer, "use_dropout")
            assert trainer.use_dropout is True
            assert hasattr(trainer, "adaptive_lr")
            assert trainer.adaptive_lr is True
            print("   ✅ Fase 3: PER, Noisy Networks, Dropout y LR adaptativo activos")

            # Verificar componentes de Fase 4 (Evaluación y métricas)
            print("📊 Fase 4: Verificando sistema de evaluación...")
            assert hasattr(trainer, "evaluator")
            assert trainer.evaluator is not None
            assert hasattr(trainer, "evaluation_frequency")
            assert hasattr(trainer, "_simulate_evaluation")

            # Probar el sistema de evaluación
            evaluation_result = trainer._simulate_evaluation()
            assert isinstance(evaluation_result, dict)
            assert "mean_reward" in evaluation_result
            print("   ✅ Fase 4: Sistema de evaluación y métricas funcionando")

            # Verificar arquitectura del modelo
            print("🏗️ Verificando arquitectura completa del modelo...")
            # Verificar arquitectura usando summary del modelo
            model_summary: list[str] = []
            trainer.model.summary(print_fn=model_summary.append)
            model_text = "\n".join(model_summary)

            # Verificar que es arquitectura Dueling
            assert "Dueling_DQN" in model_text
            # Verificar que tiene Dropout
            assert "Dropout" in model_text
            # Verificar número de parámetros esperado
            assert "477905" in model_text or "477,905" in model_text
            print("   ✅ Arquitectura: Dueling DQN con Dropout y parámetros correctos")

            # Verificar configuración de memoria
            print("💾 Verificando configuración de memoria...")
            if trainer.use_prioritized_replay:
                from src.traffic_system.decision.DQN.dqn_trainer import (
                    PrioritizedReplayBuffer,
                )

                assert isinstance(trainer.memory_buffer, PrioritizedReplayBuffer)
                print("   ✅ Memoria: Prioritized Experience Replay configurado")
            else:
                print("   ⚠️ Memoria: Replay buffer estándar")

            # Verificar configuración de evaluación
            print("🧪 Verificando configuración de evaluación...")
            assert trainer.evaluator.model_name.startswith("DQN_F1-2-3-4_")
            assert trainer.evaluation_frequency > 0
            print(f"   ✅ Evaluación: Cada {trainer.evaluation_frequency} épocas")

            # Simular registro de métricas
            print("📈 Simulando registro de métricas...")
            trainer.evaluator.record_training_step(
                episode=1,
                reward=20.5,
                loss=0.15,
                epsilon=0.8,
                learning_rate=0.001,
                avg_q_value=3.2,
                episode_length=200,
                waiting_time=35.0,
                throughput=12.5,
            )

            assert len(trainer.evaluator.training_metrics["episodes"]) == 1
            assert trainer.evaluator.training_metrics["rewards"][0] == 20.5
            print("   ✅ Métricas: Registro funcionando correctamente")

        print("\n🎉 ¡TODAS LAS FASES FUNCIONANDO CORRECTAMENTE!")
        return True


def test_configuration_consistency() -> bool:
    """Verificar consistencia de configuraciones entre fases."""
    print("\n🔧 Verificando consistencia de configuraciones...")

    from src.traffic_system.core.config_loader import load_app_settings

    try:
        settings = load_app_settings()
        config = settings.decision.entrenamiento

        # Verificar configuraciones de Fase 2
        assert hasattr(config, "use_double_dqn")
        assert hasattr(config, "use_dueling_dqn")
        assert hasattr(config, "target_update_frequency")
        print("   ✅ Configuración Fase 2: Double DQN y Dueling DQN")

        # Verificar configuraciones de Fase 3
        assert hasattr(config, "use_prioritized_replay")
        assert hasattr(config, "per_alpha")
        assert hasattr(config, "use_noisy_networks")
        assert hasattr(config, "use_dropout")
        assert hasattr(config, "adaptive_lr")
        print("   ✅ Configuración Fase 3: Optimizaciones avanzadas")

        # Verificar configuraciones de Fase 4
        assert hasattr(config, "enable_evaluation")
        assert hasattr(config, "evaluation_episodes")
        assert hasattr(config, "evaluation_frequency")
        print("   ✅ Configuración Fase 4: Sistema de evaluación")

        print("🎯 Todas las configuraciones están presentes y correctas")
        return True

    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False


def test_model_architecture_details() -> bool:
    """Test detallado de la arquitectura del modelo."""
    print("\n🏗️ Verificando detalles de arquitectura del modelo...")

    with patch("src.traffic_system.decision.DQN.dqn_trainer.DecisionAPI") as mock_api:
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        # Configurar respuestas mínimas
        mock_api_instance.get_wait_times.return_value = {
            f"zona_{i}": 30 for i in range(1, 13)
        }
        mock_api_instance.get_quantities.return_value = {
            f"zona_{i}": 5 for i in range(1, 13)
        }

        with patch(
            "src.traffic_system.decision.DQN.dqn_trainer.DQNTrainer._train_agent"
        ):
            from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

            trainer = DQNTrainer(auto_train=False)

            # Inicializar el modelo manualmente ya que auto_train=False
            if trainer.model is None:
                trainer.model = trainer._build_model()
                trainer.target_model = trainer._build_model()
                trainer.target_model.set_weights(trainer.model.get_weights())

            # Verificar que el modelo existe antes de acceder a sus propiedades
            assert (
                trainer.model is not None
            ), "Model must be initialized for architecture test"

            # Verificar entrada del modelo
            assert trainer.model.input_shape == (None, 48)
            print("   ✅ Entrada: 48 características (actual + histórico)")

            # Verificar salida del modelo
            assert trainer.model.output_shape == (None, 16)
            print("   ✅ Salida: 16 acciones (4^2 combinaciones de semáforos)")

            # Verificar que tiene las capas necesarias
            layer_names = [layer.name for layer in trainer.model.layers]

            # Verificar componentes Dueling
            dueling_components = [
                "advantage",
                "value",
                "advantage_mean",
                "advantage_centered",
                "q_values",
            ]
            for component in dueling_components:
                assert any(
                    component in name for name in layer_names
                ), f"Falta componente Dueling: {component}"
            print("   ✅ Arquitectura Dueling: Todas las capas presentes")

            # Verificar Dropout
            dropout_layers = [name for name in layer_names if "dropout" in name.lower()]
            assert len(dropout_layers) > 0, "No se encontraron capas Dropout"
            print(f"   ✅ Regularización: {len(dropout_layers)} capas Dropout")

            # Verificar red target (Double DQN)
            if trainer.use_double_dqn:
                assert trainer.target_model is not None
                assert trainer.target_model.get_weights() is not None
                print("   ✅ Double DQN: Red target inicializada")

            print("🏗️ Arquitectura del modelo completamente verificada")
            return True


if __name__ == "__main__":
    print("🚀 INICIANDO VERIFICACIÓN COMPLETA DE TODAS LAS FASES DQN")
    print("=" * 70)

    # Ejecutar todos los tests
    success = True

    try:
        success &= test_all_phases_integration()
        success &= test_configuration_consistency()
        success &= test_model_architecture_details()

        if success:
            print("\n" + "=" * 70)
            print("✅ ¡VERIFICACIÓN COMPLETA EXITOSA!")
            print("=" * 70)
            print("🎯 FASE 1: Arquitectura base DQN ✅")
            print("🎯 FASE 2: Double DQN + Dueling DQN ✅")
            print("🎯 FASE 3: PER + Noisy Networks + Dropout + LR Adaptativo ✅")
            print("🎯 FASE 4: Sistema de Evaluación y Métricas ✅")
            print("=" * 70)
            print("🚀 TODAS LAS MEJORAS DQN IMPLEMENTADAS Y FUNCIONANDO")
            print("📊 Sistema listo para entrenamiento avanzado")
            print("=" * 70)
        else:
            print("\n❌ ALGUNOS TESTS FALLARON")

    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA VERIFICACIÓN: {e}")
        success = False

    exit(0 if success else 1)
