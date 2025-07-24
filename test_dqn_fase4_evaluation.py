"""
🧪 Test de Fase 4: Sistema de Evaluación y Métricas DQN

Verifica que el sistema de evaluación funcione correctamente con todas las métricas implementadas.
"""

import os
import tempfile
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np

# Configurar entorno de prueba
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Silenciar logs de TensorFlow


def test_dqn_evaluation_system() -> bool:
    """Test del sistema de evaluación DQN Fase 4."""
    print("🧪 Iniciando test del sistema de evaluación DQN (Fase 4)...")

    with patch("src.traffic_system.decision.DQN.dqn_trainer.DecisionAPI") as mock_api:
        # Configurar mock de la API
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        # Configurar respuestas simuladas
        mock_api_instance.get_wait_times.return_value = {
            "zona_" + str(i): np.random.randint(0, 60) for i in range(1, 13)
        }
        mock_api_instance.get_quantities.return_value = {
            "zona_" + str(i): np.random.randint(1, 10) for i in range(1, 13)
        }
        mock_api_instance.advance_simulation.return_value = {"simulation_ended": False}
        mock_api_instance.set_traffic_light_states.return_value = {"success": True}

        # Importar después del mock para evitar problemas de inicialización
        from src.traffic_system.decision.DQN.evaluation_metrics import DQNEvaluator

        # Test 1: Verificar inicialización del evaluador
        print("📊 Test 1: Inicialización del sistema de evaluación")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Crear un evaluador independiente para testing
            evaluator = DQNEvaluator(
                config=MagicMock(
                    entrenamiento=MagicMock(
                        evaluation_episodes=5,
                        evaluation_frequency=3,
                        metrics_window_size=50,
                        statistical_tests=True,
                        generate_plots=True,
                        save_evaluation_data=True,
                    )
                ),
                results_dir=temp_dir,
                model_name="Test_DQN_F4",
            )

            assert evaluator is not None
            assert evaluator.model_name == "Test_DQN_F4"
            assert evaluator.window_size == 50
            print("   ✅ Evaluador inicializado correctamente")

        # Test 2: Verificar registro de métricas
        print("📈 Test 2: Registro de métricas de entrenamiento")

        evaluator.record_training_step(
            episode=1,
            reward=15.5,
            loss=0.25,
            epsilon=0.8,
            learning_rate=0.001,
            avg_q_value=2.3,
            episode_length=150,
            waiting_time=45.2,
            throughput=8.7,
        )

        assert len(evaluator.training_metrics["episodes"]) == 1
        assert evaluator.training_metrics["rewards"][0] == 15.5
        assert evaluator.training_metrics["losses"][0] == 0.25
        print("   ✅ Métricas registradas correctamente")

        # Test 3: Verificar evaluación simulada
        print("🎯 Test 3: Evaluación de agente simulada")

        # Agregar más datos para tener ventana
        for i in range(2, 6):
            evaluator.record_training_step(
                episode=i,
                reward=15.0 + i,
                loss=0.3 - i * 0.01,
                epsilon=0.8 - i * 0.1,
                learning_rate=0.001,
                avg_q_value=2.0 + i * 0.1,
                episode_length=150 + i * 5,
                waiting_time=45.0 - i,
                throughput=8.0 + i * 0.5,
            )

        # Mock del agente para evaluación
        mock_agent = MagicMock()
        mock_agent.epsilon = 0.1
        mock_agent.act.return_value = np.random.randint(0, 4)

        # Mock del entorno
        mock_env = MagicMock()
        mock_env.reset.return_value = np.random.rand(48)
        mock_env.step.return_value = (
            np.random.rand(48),  # next_state
            np.random.uniform(10, 20),  # reward
            np.random.choice([True, False]),  # done
            {
                "waiting_time": np.random.uniform(30, 60),
                "throughput": np.random.uniform(5, 15),
            },  # info
        )

        # Simular que el entorno termina después de algunos pasos
        step_count = 0

        def mock_step_side_effect(*args: Any, **kwargs: Any) -> tuple:
            nonlocal step_count
            step_count += 1
            done = step_count > 10
            return (
                np.random.rand(48),
                np.random.uniform(10, 20),
                done,
                {
                    "waiting_time": np.random.uniform(30, 60),
                    "throughput": np.random.uniform(5, 15),
                },
            )

        mock_env.step.side_effect = mock_step_side_effect

        # Ejecutar evaluación
        evaluation_metrics = evaluator.evaluate_agent(
            mock_agent, mock_env, num_episodes=3
        )

        assert "mean_reward" in evaluation_metrics
        assert "std_reward" in evaluation_metrics
        assert "mean_waiting_time" in evaluation_metrics
        assert evaluation_metrics["total_episodes"] == 3
        print(
            f"   ✅ Evaluación completada: Reward promedio = {evaluation_metrics['mean_reward']:.2f}"
        )

        # Test 4: Verificar comparación con baseline
        print("📊 Test 4: Comparación con baseline")

        # Establecer baseline
        evaluator.set_baseline_from_current()
        assert evaluator.baseline_metrics is not None

        # Simular métricas mejoradas
        improved_metrics = {
            "mean_reward": evaluation_metrics["mean_reward"] * 1.1,  # 10% mejor
            "mean_waiting_time": evaluation_metrics["mean_waiting_time"]
            * 0.9,  # 10% menos tiempo
            "mean_throughput": evaluation_metrics.get("mean_throughput", 10.0)
            * 1.05,  # 5% mejor throughput
        }

        comparison = evaluator.compare_with_baseline(improved_metrics)
        assert comparison["has_baseline"] is True
        assert comparison["reward_improvement_pct"] > 0
        print(f"   ✅ Mejora en reward: {comparison['reward_improvement_pct']:.1f}%")

        # Test 5: Verificar tests estadísticos
        print("📊 Test 5: Tests estadísticos")

        current_rewards = [15.5, 16.2, 17.1, 18.0, 16.8]
        baseline_rewards = [14.0, 14.5, 15.2, 14.8, 15.1]

        stats_results = evaluator.statistical_significance_test(
            current_rewards, baseline_rewards
        )
        assert stats_results["tests_enabled"] is True
        assert "t_test" in stats_results
        assert "mann_whitney" in stats_results
        assert "cohens_d" in stats_results
        print(f"   ✅ Test t: p={stats_results['t_test']['p_value']:.4f}")
        print(
            f"   ✅ Cohen's d: {stats_results['cohens_d']:.3f} ({stats_results['effect_size']})"
        )

        # Test 6: Verificar generación de gráficos (sin realmente generar)
        print("📊 Test 6: Sistema de gráficos")

        with (
            patch("matplotlib.pyplot.savefig") as mock_savefig,
            patch("matplotlib.pyplot.close") as mock_close,
        ):
            evaluator.generate_plots()
            mock_savefig.assert_called_once()
            mock_close.assert_called_once()
        print("   ✅ Sistema de gráficos verificado")

        # Test 7: Verificar guardado de métricas
        print("💾 Test 7: Guardado de métricas")

        with tempfile.TemporaryDirectory() as temp_dir:
            evaluator.session_dir = temp_dir
            metrics_path = evaluator.save_metrics()

            assert os.path.exists(metrics_path)
            assert metrics_path.endswith(".json")
        print("   ✅ Métricas guardadas correctamente")

        print("\n🎉 ¡Todos los tests del sistema de evaluación pasaron exitosamente!")
        print("✅ Sistema de evaluación Fase 4 funcionando correctamente")

        return True


def test_integration_with_trainer() -> bool:
    """Test del DQNTrainer con sistema de evaluación integrado."""
    print("\n🧪 Test de integración: DQNTrainer con evaluación...")

    with patch("src.traffic_system.decision.DQN.dqn_trainer.DecisionAPI") as mock_api:
        # Configurar mock básico
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        # Respuestas consistentes para evitar errores
        mock_api_instance.get_wait_times.return_value = {
            f"zona_{i}": 30 for i in range(1, 13)
        }
        mock_api_instance.get_quantities.return_value = {
            f"zona_{i}": 5 for i in range(1, 13)
        }
        mock_api_instance.advance_simulation.return_value = {
            "simulation_ended": True
        }  # Terminar rápido
        mock_api_instance.set_traffic_light_states.return_value = {"success": True}

        # Patch para evitar entrenamiento real
        with patch(
            "src.traffic_system.decision.DQN.dqn_trainer.DQNTrainer._train_agent"
        ):
            from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

            # Crear trainer con auto_train=False para control manual
            trainer = DQNTrainer(auto_train=False)

            # Verificar que el evaluador fue inicializado
            assert hasattr(trainer, "evaluator")
            assert trainer.evaluator is not None
            assert hasattr(trainer, "evaluation_frequency")

            print("   ✅ DQNTrainer inicializado con sistema de evaluación")

            # Verificar que el método de evaluación simulada existe
            assert hasattr(trainer, "_simulate_evaluation")

            # Probar evaluación simulada
            evaluation_result = trainer._simulate_evaluation()
            assert isinstance(evaluation_result, dict)
            assert "mean_reward" in evaluation_result

            print("   ✅ Sistema de evaluación integrado correctamente")

        print("🎉 ¡Test de integración completado exitosamente!")
        return True


if __name__ == "__main__":
    # Ejecutar tests
    test_dqn_evaluation_system()
    test_integration_with_trainer()

    print("\n" + "=" * 60)
    print("✅ FASE 4: SISTEMA DE EVALUACIÓN Y MÉTRICAS COMPLETADO")
    print("=" * 60)
    print("🧪 Sistema de evaluación robusto implementado")
    print("📊 Métricas estadísticas y comparaciones funcionando")
    print("📈 Gráficos y visualizaciones integrados")
    print("💾 Guardado y carga de datos implementado")
    print("🎯 Integración con DQNTrainer exitosa")
    print("=" * 60)
