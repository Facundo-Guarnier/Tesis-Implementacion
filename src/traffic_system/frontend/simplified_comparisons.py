"""
Página de comparaciones simplificada y enfocada en demostrar superioridad del DQN.

Este módulo reemplaza la versión compleja con una interfaz clara que muestra
en 30 segundos que DQN es superior a tiempos fijos.
"""

import glob
import os
import sqlite3

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_simplified_comparisons_page() -> None:
    """Renderizar página simplificada de comparaciones S1 vs S2."""

    # Encabezado claro y directo
    st.markdown(
        """
    # 🎯 DQN vs Tiempos Fijos: Resultados de la Comparación

    **Objetivo:** Demostrar que el sistema inteligente DQN supera a los semáforos tradicionales de tiempos fijos.
    """
    )

    try:
        # Buscar bases de datos de comparaciones
        db_pattern = "results/comparison*.db"
        db_files = glob.glob(db_pattern)

        if not db_files:
            st.error(
                """
            ### 📭 No hay datos de comparación disponibles

            **Para generar datos:**
            1. Activar `sumo.comparacion_export.enabled` en Configuración
            2. Ejecutar simulación con `sumo.comparar=True`
            3. Los resultados aparecerán aquí automáticamente
            """
            )
            return

        # Usar la base de datos más reciente
        latest_db = max(db_files, key=os.path.getmtime)
        st.sidebar.success(f"📊 Usando datos de: `{os.path.basename(latest_db)}`")

        # Conectar a la base de datos
        conn = sqlite3.connect(latest_db)

        # Cargar datos esenciales
        metrics_df = pd.read_sql_query(
            "SELECT timestamp_simulacion, s1_tiempo_actual, s2_tiempo_actual, "
            "s1_vehiculos_actual, s2_vehiculos_actual FROM comparacion_metricas "
            "ORDER BY timestamp_simulacion",
            conn,
        )

        summary_df = pd.read_sql_query("SELECT * FROM comparacion_resumenes", conn)
        conn.close()

        if metrics_df.empty:
            st.warning("📭 No se encontraron datos de métricas")
            return

        # =============================================================================
        # RESUMEN EJECUTIVO PROMINENTE
        # =============================================================================

        # Calcular métricas principales
        tiempo_dqn = metrics_df["s1_tiempo_actual"].mean()
        tiempo_fijo = metrics_df["s2_tiempo_actual"].mean()
        vehiculos_dqn = metrics_df["s1_vehiculos_actual"].mean()
        vehiculos_fijo = metrics_df["s2_vehiculos_actual"].mean()

        mejora_tiempo = (
            ((tiempo_fijo - tiempo_dqn) / tiempo_fijo) * 100 if tiempo_fijo > 0 else 0
        )
        mejora_vehiculos = (
            ((vehiculos_fijo - vehiculos_dqn) / vehiculos_fijo) * 100
            if vehiculos_fijo > 0
            else 0
        )

        # Mostrar resultado principal de forma prominente
        st.markdown("---")

        if mejora_tiempo > 0:
            st.success(
                f"""
            ## 🎉 ¡DQN ES SUPERIOR!

            ### El sistema inteligente DQN reduce **{mejora_tiempo:.1f}%** el tiempo de espera
            """
            )
        else:
            st.error(
                f"""
            ## ⚠️ Los tiempos fijos funcionan mejor

            ### DQN tiene **{abs(mejora_tiempo):.1f}%** más tiempo de espera
            """
            )

        # Métricas principales en columnas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="⏱️ Tiempo de Espera Promedio",
                value=f"DQN: {tiempo_dqn:.1f}s",
                delta=f"{tiempo_fijo - tiempo_dqn:.1f}s mejor que fijo",
                delta_color="inverse",
            )

        with col2:
            st.metric(
                label="🚗 Vehículos Esperando",
                value=f"DQN: {vehiculos_dqn:.1f}",
                delta=f"{vehiculos_fijo - vehiculos_dqn:.1f} menos que fijo",
                delta_color="inverse",
            )

        with col3:
            eficiencia_general = (mejora_tiempo + mejora_vehiculos) / 2
            st.metric(
                label="📊 Eficiencia General",
                value=f"+{eficiencia_general:.1f}%",
                delta="DQN vs Tiempos Fijos",
            )

        st.markdown("---")

        # =============================================================================
        # GRÁFICOS COMPARATIVOS SIMPLES
        # =============================================================================

        st.markdown("## 📈 Evolución Temporal: DQN vs Tiempos Fijos")
        st.markdown(
            "**Interpretación:** La línea azul (DQN) debe estar consistentemente por debajo de la roja (Fijo) para demostrar superioridad."
        )

        # Convertir timestamp a minutos para mejor legibilidad
        metrics_df["minuto"] = (
            metrics_df["timestamp_simulacion"]
            - metrics_df["timestamp_simulacion"].min()
        ) / 60

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ⏱️ Tiempo de Espera")

            fig_tiempo = go.Figure()

            # Línea DQN
            fig_tiempo.add_trace(
                go.Scatter(
                    x=metrics_df["minuto"],
                    y=metrics_df["s1_tiempo_actual"],
                    mode="lines",
                    name="🤖 DQN (Inteligente)",
                    line=dict(color="#1f77b4", width=3),
                    hovertemplate="DQN: %{y:.1f}s<br>Minuto: %{x:.1f}<extra></extra>",
                )
            )

            # Línea Tiempos Fijos
            fig_tiempo.add_trace(
                go.Scatter(
                    x=metrics_df["minuto"],
                    y=metrics_df["s2_tiempo_actual"],
                    mode="lines",
                    name="⏰ Tiempos Fijos",
                    line=dict(color="#d62728", width=3),
                    hovertemplate="Fijo: %{y:.1f}s<br>Minuto: %{x:.1f}<extra></extra>",
                )
            )

            fig_tiempo.update_layout(
                title="Tiempo de Espera por Minuto",
                xaxis_title="Tiempo (minutos)",
                yaxis_title="Tiempo de Espera (segundos)",
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )

            st.plotly_chart(fig_tiempo, use_container_width=True)

            # Interpretación rápida
            if tiempo_dqn < tiempo_fijo:
                st.success(
                    f"✅ DQN consistentemente mejor: {tiempo_dqn:.1f}s vs {tiempo_fijo:.1f}s"
                )
            else:
                st.error(
                    f"❌ Tiempos fijos mejor: {tiempo_fijo:.1f}s vs {tiempo_dqn:.1f}s"
                )

        with col2:
            st.markdown("### 🚗 Congestión Vehicular")

            fig_vehiculos = go.Figure()

            # Línea DQN
            fig_vehiculos.add_trace(
                go.Scatter(
                    x=metrics_df["minuto"],
                    y=metrics_df["s1_vehiculos_actual"],
                    mode="lines",
                    name="🤖 DQN (Inteligente)",
                    line=dict(color="#1f77b4", width=3),
                    hovertemplate="DQN: %{y:.1f} vehículos<br>Minuto: %{x:.1f}<extra></extra>",
                )
            )

            # Línea Tiempos Fijos
            fig_vehiculos.add_trace(
                go.Scatter(
                    x=metrics_df["minuto"],
                    y=metrics_df["s2_vehiculos_actual"],
                    mode="lines",
                    name="⏰ Tiempos Fijos",
                    line=dict(color="#d62728", width=3),
                    hovertemplate="Fijo: %{y:.1f} vehículos<br>Minuto: %{x:.1f}<extra></extra>",
                )
            )

            fig_vehiculos.update_layout(
                title="Vehículos Esperando por Minuto",
                xaxis_title="Tiempo (minutos)",
                yaxis_title="Número de Vehículos",
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )

            st.plotly_chart(fig_vehiculos, use_container_width=True)

            # Interpretación rápida
            if vehiculos_dqn < vehiculos_fijo:
                st.success(
                    f"✅ DQN reduce congestión: {vehiculos_dqn:.1f} vs {vehiculos_fijo:.1f} vehículos"
                )
            else:
                st.error(
                    f"❌ Tiempos fijos reducen más: {vehiculos_fijo:.1f} vs {vehiculos_dqn:.1f} vehículos"
                )

        # =============================================================================
        # TABLA RESUMEN FINAL
        # =============================================================================

        st.markdown("---")
        st.markdown("## 📋 Resumen Comparativo Final")

        # Crear tabla simple pero impactante
        comparison_data = {
            "Métrica": [
                "⏱️ Tiempo de Espera Promedio",
                "🚗 Vehículos Esperando (Promedio)",
                "📊 Eficiencia General",
            ],
            "🤖 DQN (Inteligente)": [
                f"{tiempo_dqn:.1f} segundos",
                f"{vehiculos_dqn:.1f} vehículos",
                "Sistema base",
            ],
            "⏰ Tiempos Fijos": [
                f"{tiempo_fijo:.1f} segundos",
                f"{vehiculos_fijo:.1f} vehículos",
                "Sistema de referencia",
            ],
            "📈 Mejora con DQN": [
                (
                    f"{mejora_tiempo:+.1f}%"
                    if mejora_tiempo >= 0
                    else f"{mejora_tiempo:.1f}%"
                ),
                (
                    f"{mejora_vehiculos:+.1f}%"
                    if mejora_vehiculos >= 0
                    else f"{mejora_vehiculos:.1f}%"
                ),
                (
                    f"{eficiencia_general:+.1f}%"
                    if eficiencia_general >= 0
                    else f"{eficiencia_general:.1f}%"
                ),
            ],
        }

        comparison_df = pd.DataFrame(comparison_data)

        # Mostrar tabla con estilo
        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Métrica": st.column_config.TextColumn("Métrica", width="medium"),
                "🤖 DQN (Inteligente)": st.column_config.TextColumn(
                    "🤖 DQN (Inteligente)", width="medium"
                ),
                "⏰ Tiempos Fijos": st.column_config.TextColumn(
                    "⏰ Tiempos Fijos", width="medium"
                ),
                "📈 Mejora con DQN": st.column_config.TextColumn(
                    "📈 Mejora con DQN", width="medium"
                ),
            },
        )

        # =============================================================================
        # CONCLUSIÓN CLARA
        # =============================================================================

        st.markdown("---")

        if mejora_tiempo > 10 and mejora_vehiculos > 5:
            st.success(
                """
            ### 🎉 CONCLUSIÓN: DQN ES CLARAMENTE SUPERIOR

            Los datos demuestran que el sistema inteligente DQN supera consistentemente
            a los semáforos tradicionales de tiempos fijos en ambas métricas principales.
            """
            )
        elif mejora_tiempo > 0 or mejora_vehiculos > 0:
            st.info(
                """
            ### ✅ CONCLUSIÓN: DQN MUESTRA MEJORAS

            El sistema DQN presenta ventajas sobre los tiempos fijos, aunque con margen
            de optimización adicional.
            """
            )
        else:
            st.warning(
                """
            ### ⚠️ CONCLUSIÓN: NECESITA REVISIÓN

            Los tiempos fijos muestran mejor rendimiento. Revisar configuración y
            entrenamiento del modelo DQN.
            """
            )

        # Información técnica mínima
        with st.expander("ℹ️ Información técnica"):
            st.markdown(
                f"""
            **Datos analizados:**
            - {len(metrics_df)} mediciones temporales
            - Duración total: {metrics_df['minuto'].max():.1f} minutos
            - Base de datos: `{os.path.basename(latest_db)}`

            **Metodología:**
            - S1: Sistema DQN (líneas azules)
            - S2: Tiempos fijos (líneas rojas)
            - Mediciones cada 15 segundos durante la simulación
            """
            )

    except Exception as e:
        st.error(f"Error al cargar datos de comparación: {e}")
        st.markdown(
            """
        **Posibles soluciones:**
        1. Verificar que existe `results/comparison.db`
        2. Ejecutar una simulación con comparación habilitada
        3. Revisar permisos de archivos
        """
        )


if __name__ == "__main__":
    st.set_page_config(page_title="DQN vs Tiempos Fijos", page_icon="🎯", layout="wide")
    render_simplified_comparisons_page()
