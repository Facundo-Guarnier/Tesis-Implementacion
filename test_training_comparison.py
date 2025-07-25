#!/usr/bin/env python3
"""
🔍 Herramienta de Análisis de Entrenamiento DQN

Analiza archivos CSV de entrenamiento para detectar problemas de rendimiento,
learning rate decay, estabilidad de recompensas y otros métricas clave.

Uso:
    poetry run python test_training_comparison.py <archivo_csv>
    poetry run python test_training_comparison.py "datos_entrenamiento.csv"
"""

import logging
import sys
from pathlib import Path

import pandas as pd

# Configurar logging con emojis
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def analyze_learning_rate_decay(data: pd.DataFrame) -> dict[str, float]:
    """
    Analiza el comportamiento del learning rate decay.
    """
    logger.info("\n🔍 Analizando Learning Rate Decay...")

    # Filtrar datos válidos (excluir época baseline "-")
    valid_data = data[data["Epoca"] != "-"].copy()

    if len(valid_data) < 2:
        logger.warning("No hay suficientes datos de learning rate")
        return {}

    # Convertir a numérico
    valid_data["Learning Rate Actual"] = pd.to_numeric(
        valid_data["Learning Rate Actual"], errors="coerce"
    )

    # Calcular estadísticas
    initial_lr = valid_data["Learning Rate Actual"].iloc[0]
    final_lr = valid_data["Learning Rate Actual"].iloc[-1]
    lr_drop_pct = ((initial_lr - final_lr) / initial_lr) * 100

    # Analizar decay por época
    lr_changes = valid_data["Learning Rate Actual"].pct_change().dropna()
    avg_decay_per_epoch = lr_changes.mean() * -100  # Convertir a positivo

    logger.info(f"📊 LR inicial: {initial_lr:.8f}")
    logger.info(f"📊 LR final: {final_lr:.8f}")
    logger.info(f"📊 Caída total: {lr_drop_pct:.1f}%")
    logger.info(f"📊 Decay promedio por época: {avg_decay_per_epoch:.2f}%")

    # Evaluar problemas
    if lr_drop_pct > 95:
        logger.error(f"❌ COLAPSO CATASTRÓFICO: LR cayó {lr_drop_pct:.1f}% (>95%)")
    elif lr_drop_pct > 75:
        logger.warning(f"⚠️ Decay muy agresivo: {lr_drop_pct:.1f}%")
    elif lr_drop_pct > 50:
        logger.info(f"📉 Decay normal-alto: {lr_drop_pct:.1f}%")
    else:
        logger.info(f"✅ Decay controlado: {lr_drop_pct:.1f}%")

    return {
        "initial_lr": initial_lr,
        "final_lr": final_lr,
        "lr_drop_pct": lr_drop_pct,
        "avg_decay_per_epoch": avg_decay_per_epoch,
        "is_catastrophic": lr_drop_pct > 95,
    }


def analyze_performance_degradation(data: pd.DataFrame) -> dict[str, float]:
    """
    Analiza la degradación de rendimiento durante el entrenamiento.
    """
    logger.info("\n🔍 Analizando degradación de rendimiento...")

    # Filtrar datos válidos (excluir época baseline "-")
    valid_data = data[data["Epoca"] != "-"].copy()

    if len(valid_data) < 2:
        logger.warning("No hay suficientes datos de rendimiento")
        return {}

    # Convertir a numérico
    valid_data["Duración (segundos)"] = pd.to_numeric(
        valid_data["Duración (segundos)"], errors="coerce"
    )
    valid_data["Pasos por Segundo"] = pd.to_numeric(
        valid_data["Pasos por Segundo"], errors="coerce"
    )
    valid_data["Tiempo Inferencia Promedio"] = pd.to_numeric(
        valid_data["Tiempo Inferencia Promedio"], errors="coerce"
    )
    valid_data["Memoria RAM Proceso (MB)"] = pd.to_numeric(
        valid_data["Memoria RAM Proceso (MB)"], errors="coerce"
    )

    # Calcular métricas
    first_duration = valid_data["Duración (segundos)"].iloc[0]
    last_duration = valid_data["Duración (segundos)"].iloc[-1]
    duration_change_pct = ((last_duration - first_duration) / first_duration) * 100

    first_sps = valid_data["Pasos por Segundo"].iloc[0]
    last_sps = valid_data["Pasos por Segundo"].iloc[-1]
    sps_change_pct = ((last_sps - first_sps) / first_sps) * 100

    first_inference = valid_data["Tiempo Inferencia Promedio"].iloc[0]
    last_inference = valid_data["Tiempo Inferencia Promedio"].iloc[-1]
    inference_change_pct = ((last_inference - first_inference) / first_inference) * 100

    first_memory = valid_data["Memoria RAM Proceso (MB)"].iloc[0]
    last_memory = valid_data["Memoria RAM Proceso (MB)"].iloc[-1]
    memory_change_pct = ((last_memory - first_memory) / first_memory) * 100

    logger.info(
        f"📊 Duración por época: {first_duration:.0f}s → {last_duration:.0f}s ({duration_change_pct:+.1f}%)"
    )
    logger.info(
        f"📊 Pasos por segundo: {first_sps:.2f} → {last_sps:.2f} ({sps_change_pct:+.1f}%)"
    )
    logger.info(
        f"📊 Tiempo inferencia: {first_inference:.6f}ms → {last_inference:.6f}ms ({inference_change_pct:+.1f}%)"
    )
    logger.info(
        f"📊 Memoria RAM: {first_memory:.0f}MB → {last_memory:.0f}MB ({memory_change_pct:+.1f}%)"
    )

    # Evaluar problemas
    problems = []
    if duration_change_pct > 10:
        problems.append(f"Duración aumenta {duration_change_pct:.1f}%")
    if sps_change_pct < -10:
        problems.append(f"Pasos/s bajan {sps_change_pct:.1f}%")
    if inference_change_pct > 500:
        problems.append(f"Tiempo inferencia aumenta {inference_change_pct:.1f}%")
    if memory_change_pct > 15:
        problems.append(f"Memoria aumenta {memory_change_pct:.1f}%")

    if problems:
        logger.error(f"❌ PROBLEMAS DE RENDIMIENTO: {', '.join(problems)}")
    else:
        logger.info("✅ Rendimiento parece estable")

    return {
        "avg_duration": valid_data["Duración (segundos)"].mean(),
        "avg_sps": valid_data["Pasos por Segundo"].mean(),
        "duration_change_pct": duration_change_pct,
        "sps_change_pct": sps_change_pct,
        "inference_change_pct": inference_change_pct,
        "memory_change_pct": memory_change_pct,
        "has_performance_issues": len(problems) > 0,
    }


def analyze_reward_stability(data: pd.DataFrame) -> dict[str, float]:
    """
    Analiza la estabilidad de las recompensas.
    """
    logger.info("\n🔍 Analizando estabilidad de recompensas...")

    valid_data = data[data["Epoca"] != "-"].copy()

    if len(valid_data) < 3:
        logger.warning("No hay suficientes datos de recompensas")
        return {}

    rewards = pd.to_numeric(
        valid_data["Recompensa Acumulada"], errors="coerce"
    ).dropna()

    if len(rewards) < 3:
        logger.warning("No hay suficientes recompensas válidas")
        return {}

    # Calcular estadísticas
    mean_reward = rewards.mean()
    std_reward = rewards.std()
    cv = (std_reward / abs(mean_reward)) * 100  # Coeficiente de variación

    # Buscar saltos dramáticos
    reward_changes = rewards.pct_change().dropna()
    max_change = reward_changes.abs().max() * 100

    # Encontrar el cambio más dramático
    max_change_idx = reward_changes.abs().idxmax()
    max_change_epoch = valid_data.loc[max_change_idx, "Epoca"]

    logger.info(f"📊 Recompensa promedio: {mean_reward:,.0f}")
    logger.info(f"📊 Desviación estándar: {std_reward:,.0f}")
    logger.info(f"📊 Coeficiente de variación: {cv:.1f}%")
    logger.info(f"📊 Mayor cambio: {max_change:.1f}% en época {max_change_epoch}")

    # Evaluar estabilidad
    if cv > 50:
        logger.error(f"❌ ALTA INESTABILIDAD: CV = {cv:.1f}% (>50%)")
    elif cv > 25:
        logger.warning(f"⚠️ Inestabilidad moderada: CV = {cv:.1f}%")
    else:
        logger.info("✅ Recompensas relativamente estables")

    return {
        "mean_reward": mean_reward,
        "std_reward": std_reward,
        "coefficient_variation": cv,
        "max_change_pct": max_change,
        "is_unstable": cv > 50,
    }


def analyze_q_values_evolution(data: pd.DataFrame) -> dict[str, float]:
    """
    Analiza la evolución de los Q-values durante el entrenamiento.
    """
    logger.info("\n🔍 Analizando evolución de Q-values...")

    valid_data = data[data["Epoca"] != "-"].copy()

    if len(valid_data) < 3:
        logger.warning("No hay suficientes datos de Q-values")
        return {}

    # Convertir a numérico
    q_avg = pd.to_numeric(valid_data["Q-Value Promedio"], errors="coerce").dropna()
    q_max = pd.to_numeric(valid_data["Q-Value Máximo"], errors="coerce").dropna()

    if len(q_avg) < 3:
        logger.warning("No hay suficientes Q-values válidos")
        return {}

    # Calcular estadísticas
    q_avg_growth = (
        ((q_avg.iloc[-1] - q_avg.iloc[0]) / abs(q_avg.iloc[0])) * 100
        if q_avg.iloc[0] != 0
        else 0
    )
    q_max_growth = (
        ((q_max.iloc[-1] - q_max.iloc[0]) / abs(q_max.iloc[0])) * 100
        if q_max.iloc[0] != 0
        else 0
    )

    # Detectar explosión de Q-values
    q_avg_exploded = q_avg.abs().max() > 10000
    q_max_exploded = q_max.abs().max() > 100000

    logger.info(
        f"📊 Q-Value promedio: {q_avg.iloc[0]:.2f} → {q_avg.iloc[-1]:.2f} ({q_avg_growth:+.1f}%)"
    )
    logger.info(
        f"📊 Q-Value máximo: {q_max.iloc[0]:.2f} → {q_max.iloc[-1]:.2f} ({q_max_growth:+.1f}%)"
    )

    # Evaluar problemas
    if q_avg_exploded or q_max_exploded:
        logger.error("❌ EXPLOSIÓN DE Q-VALUES detectada")
    elif abs(q_avg_growth) > 1000:
        logger.warning("⚠️ Crecimiento muy alto de Q-values")
    else:
        logger.info("✅ Q-values en rango razonable")

    return {
        "q_avg_initial": q_avg.iloc[0],
        "q_avg_final": q_avg.iloc[-1],
        "q_max_initial": q_max.iloc[0],
        "q_max_final": q_max.iloc[-1],
        "q_avg_growth": q_avg_growth,
        "q_max_growth": q_max_growth,
        "has_explosion": q_avg_exploded or q_max_exploded,
    }


def create_summary_report(
    lr_analysis: dict, perf_analysis: dict, reward_analysis: dict, q_analysis: dict
) -> None:
    """
    Crea un reporte resumen de todos los análisis.
    """
    logger.info("\n" + "=" * 60)
    logger.info("📋 RESUMEN EJECUTIVO DEL ENTRENAMIENTO")
    logger.info("=" * 60)

    # Estado general
    issues = []
    successes = []

    # Learning Rate
    if lr_analysis.get("is_catastrophic", False):
        issues.append("❌ Learning Rate: Colapso catastrófico")
    else:
        successes.append("✅ Learning Rate: Progresión controlada")

    # Rendimiento
    if perf_analysis.get("has_performance_issues", False):
        issues.append("❌ Rendimiento: Degradación significativa")
    else:
        successes.append("✅ Rendimiento: Estable")

    # Recompensas
    if reward_analysis.get("is_unstable", False):
        issues.append("❌ Recompensas: Alta inestabilidad")
    else:
        successes.append("✅ Recompensas: Relativamente estables")

    # Q-values
    if q_analysis.get("has_explosion", False):
        issues.append("❌ Q-Values: Explosión detectada")
    else:
        successes.append("✅ Q-Values: En rango razonable")

    # Mostrar resultados
    logger.info(f"\n🎯 ASPECTOS EXITOSOS ({len(successes)}):")
    for success in successes:
        logger.info(f"  {success}")

    if issues:
        logger.info(f"\n⚠️  PROBLEMAS DETECTADOS ({len(issues)}):")
        for issue in issues:
            logger.info(f"  {issue}")
    else:
        logger.info("\n🎉 ¡No se detectaron problemas críticos!")

    # Recomendaciones
    logger.info("\n💡 RECOMENDACIONES:")
    if lr_analysis.get("lr_drop_pct", 0) > 75:
        logger.info("  • Ajustar learning_rate_decay a un valor más conservador")
    if perf_analysis.get("inference_change_pct", 0) > 500:
        logger.info("  • Revisar complejidad del modelo o JIT compilation")
    if reward_analysis.get("coefficient_variation", 0) > 50:
        logger.info("  • Considerar ajustar exploration/exploitation balance")
    if q_analysis.get("has_explosion", False):
        logger.info("  • Implementar gradient clipping o reducir learning rate")

    logger.info("\n" + "=" * 60)


def main() -> None:
    """Función principal del análisis."""
    if len(sys.argv) != 2:
        logger.error("Uso: python test_training_comparison.py <archivo_csv>")
        sys.exit(1)

    csv_file = Path(sys.argv[1])
    if not csv_file.exists():
        logger.error(f"Archivo no encontrado: {csv_file}")
        sys.exit(1)

    logger.info(f"🔍 Analizando archivo: {csv_file}")

    try:
        # Cargar datos
        data = pd.read_csv(csv_file)
        logger.info(
            f"📊 Datos cargados: {len(data)} filas, {len(data.columns)} columnas"
        )

        # Realizar análisis
        lr_analysis = analyze_learning_rate_decay(data)
        perf_analysis = analyze_performance_degradation(data)
        reward_analysis = analyze_reward_stability(data)
        q_analysis = analyze_q_values_evolution(data)

        # Crear reporte resumen
        create_summary_report(lr_analysis, perf_analysis, reward_analysis, q_analysis)

    except Exception as e:
        logger.error(f"Error durante el análisis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
