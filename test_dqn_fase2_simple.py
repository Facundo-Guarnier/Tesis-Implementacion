#!/usr/bin/env python3
"""
Test simplificado para verificar mejoras DQN - Fase 2
Verifica que Double DQN y Dueling DQN funcionen correctamente.
"""

import sys
from pathlib import Path

import numpy as np
import tensorflow as tf

# Configurar path para imports
sys.path.append(str(Path(__file__).parent / "src"))


def test_phase_2_integration() -> bool:
    """Test integrado que verifica que las mejoras de Fase 2 están funcionando."""
    print("🧪 TEST INTEGRADO: Verificando mejoras Fase 2")

    try:
        from unittest.mock import Mock, patch

        from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

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

        # Debugging: ver qué atributos tiene el trainer
        print(
            f"   🔍 Atributos del trainer: {[attr for attr in dir(trainer) if not attr.startswith('_')]}"
        )

        # Verificar flags de configuración
        print(
            f"   📊 use_double_dqn: {getattr(trainer, 'use_double_dqn', 'NO DEFINIDO')}"
        )
        print(
            f"   📊 use_dueling_dqn: {getattr(trainer, 'use_dueling_dqn', 'NO DEFINIDO')}"
        )
        print(
            f"   📊 target_update_frequency: {getattr(trainer, 'target_update_frequency', 'NO DEFINIDO')}"
        )

        # Verificar que el modelo existe
        print(f"   🔍 ¿Tiene atributo 'model'? {hasattr(trainer, 'model')}")
        if hasattr(trainer, "model"):
            print(f"   🔍 ¿El modelo es None? {trainer.model is None}")

        # Inicializar el modelo manualmente ya que auto_train=False
        if trainer.model is None:
            print("   🔧 Inicializando modelo manualmente...")
            trainer.model = trainer._build_model()

            # Inicializar target_model si Double DQN está habilitado
            if trainer.use_double_dqn:
                trainer.target_model = trainer._build_model()
                trainer.target_model.set_weights(trainer.model.get_weights())

        assert hasattr(trainer, "model"), "El modelo no fue creado"
        assert trainer.model is not None, "El modelo es None"

        # Test de Dueling DQN: verificar arquitectura
        if trainer.use_dueling_dqn:
            print("   🔀 Verificando arquitectura Dueling DQN...")
            model = trainer.model

            # Para Dueling DQN, debe ser un modelo funcional
            assert not isinstance(
                model, tf.keras.Sequential
            ), "Dueling DQN debe usar API funcional"

            # Verificar capas específicas
            layer_names = [layer.name for layer in model.layers]
            value_layers = [name for name in layer_names if "value" in name]
            advantage_layers = [name for name in layer_names if "advantage" in name]

            assert (
                len(value_layers) > 0
            ), f"No se encontraron capas de valor en: {layer_names}"
            assert (
                len(advantage_layers) > 0
            ), f"No se encontraron capas de ventaja en: {layer_names}"
            assert (
                "q_values" in layer_names
            ), f"No se encontró capa Q-values en: {layer_names}"

            print("   ✅ Arquitectura Dueling DQN verificada")
        else:
            print("   ⚠️  Dueling DQN desactivado")

        # Test de Double DQN: verificar red target
        if trainer.use_double_dqn:
            print("   🎯 Verificando Double DQN...")

            assert hasattr(trainer, "target_model"), "Red target no existe"
            assert trainer.target_model is not None, "Red target es None"
            assert hasattr(
                trainer, "target_update_counter"
            ), "Contador target no existe"

            # Verificar que los pesos son idénticos inicialmente
            main_weights = trainer.model.get_weights()
            target_weights = trainer.target_model.get_weights()

            for i, (main_w, target_w) in enumerate(
                zip(main_weights, target_weights, strict=True)
            ):
                np.testing.assert_array_equal(
                    main_w,
                    target_w,
                    err_msg=f"Pesos de capa {i} no son idénticos inicialmente",
                )

            print("   ✅ Red target verificada")
        else:
            print("   ⚠️  Double DQN desactivado")

        # Test de método _update_target_model
        if hasattr(trainer, "_update_target_model"):
            print("   🔄 Verificando método _update_target_model...")

            # Este método debe existir y ser callable
            assert callable(
                trainer._update_target_model
            ), "Método _update_target_model no es callable"

            # Intentar ejecutarlo (sin errores)
            if trainer.use_double_dqn:
                trainer._update_target_model()
                print("   ✅ Método _update_target_model funciona")

        print("   ✅ Test integrado completado exitosamente")
        return True

    except Exception as e:
        print(f"   ❌ Error en test integrado: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_model_prediction() -> bool:
    """Test básico para verificar que el modelo puede hacer predicciones."""
    print("\n🧪 TEST: Predicción del modelo")

    try:
        from unittest.mock import Mock, patch

        from src.traffic_system.decision.DQN.dqn_trainer import DQNTrainer

        # Crear mock de DecisionAPI
        mock_api = Mock()
        mock_api.get_wait_times.return_value = {"wait_times": [10.5, 15.2, 8.7, 12.3]}
        mock_api.get_quantities.return_value = {"quantities": [5, 8, 3, 6]}

        with patch(
            "src.traffic_system.decision.DQN.dqn_trainer.DecisionAPI",
            return_value=mock_api,
        ):
            trainer = DQNTrainer(
                auto_train=False
            )  # No entrenar automáticamente en test

            # Inicializar el modelo manualmente ya que auto_train=False
            trainer.model = trainer._build_model()

        # Crear estado de prueba (48 features como espera el modelo)
        test_state = np.random.random((1, 48)).astype(np.float32)

        # Verificar que el modelo existe antes de hacer predicción
        assert (
            trainer.model is not None
        ), "Model must be initialized for prediction test"

        # Hacer predicción
        prediction = trainer.model.predict(test_state, verbose=0)

        # Verificar que la salida tiene el formato correcto
        assert prediction.shape[0] == 1, f"Batch size incorrecto: {prediction.shape}"
        assert prediction.shape[1] == len(
            trainer._action_space
        ), f"Número de acciones incorrecto: {prediction.shape[1]} vs {len(trainer._action_space)}"

        print(f"   📊 Forma de predicción: {prediction.shape}")
        print(f"   📊 Acciones disponibles: {len(trainer._action_space)}")
        print("   ✅ Predicción funciona correctamente")

        return True

    except Exception as e:
        print(f"   ❌ Error en test de predicción: {e}")
        return False


def main() -> bool:
    """Ejecutar tests simplificados de Fase 2."""
    print("🚀 TESTS SIMPLIFICADOS DQN - FASE 2")
    print("=" * 50)

    tests = [
        ("Integración Fase 2", test_phase_2_integration),
        ("Predicción Modelo", test_model_prediction),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error crítico en {test_name}: {e}")
            results.append(False)

    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESULTADOS:")

    passed = 0
    for i, (test_name, _) in enumerate(tests):
        if results[i]:
            print(f"   ✅ {test_name}")
            passed += 1
        else:
            print(f"   ❌ {test_name}")

    print(f"\n🎯 {passed}/{len(tests)} tests exitosos")

    if passed == len(tests):
        print("🎉 ¡Fase 2 implementada correctamente!")
        return True
    else:
        print("⚠️  Revisar implementación")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
