#!/usr/bin/env python3
"""
Script de diagnóstico para bases de datos de comparaciones.
Analiza el contenido real de las bases de datos para identificar problemas.
"""

import glob
import os
import sqlite3
from datetime import datetime

import pandas as pd


def diagnose_comparison_db():
    """Diagnosticar el contenido real de la base de datos de comparaciones."""

    print("🔍 DIAGNÓSTICO DE BASES DE DATOS DE COMPARACIONES")
    print("=" * 60)

    # Buscar bases de datos
    db_pattern = "results/comparisons/*/comparison.db"
    db_files = glob.glob(db_pattern)

    if not db_files:
        print("❌ No se encontraron bases de datos de comparación")
        print(f"📁 Patrón de búsqueda: {db_pattern}")

        # Verificar si existe el directorio base
        base_dir = "results/comparisons"
        if os.path.exists(base_dir):
            print(f"✅ Directorio base existe: {base_dir}")
            subdirs = [
                d
                for d in os.listdir(base_dir)
                if os.path.isdir(os.path.join(base_dir, d))
            ]
            print(f"📂 Subdirectorios encontrados: {subdirs}")
        else:
            print(f"❌ Directorio base no existe: {base_dir}")

        return

    print(f"✅ Encontradas {len(db_files)} base(s) de datos")
    for i, db_file in enumerate(db_files):
        print(f"  {i+1}. {db_file}")

    # Usar la más reciente
    latest_db = max(db_files, key=lambda x: os.path.getmtime(x))
    file_time = datetime.fromtimestamp(os.path.getmtime(latest_db))
    print(f"\n🔍 Analizando la más reciente: {latest_db}")
    print(f"📅 Fecha de modificación: {file_time.strftime('%d/%m/%Y %H:%M:%S')}")

    try:
        conn = sqlite3.connect(latest_db)

        # 1. Verificar qué tablas existen
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table'", conn
        )
        print(f"\n📊 TABLAS ENCONTRADAS: {list(tables['name'])}")

        # 2. Analizar tabla de métricas temporales
        if "comparacion_metricas" in tables["name"].values:
            print("\n" + "=" * 50)
            print("🔍 ANÁLISIS DE 'comparacion_metricas'")
            print("=" * 50)

            # Esquema
            schema = pd.read_sql_query("PRAGMA table_info(comparacion_metricas)", conn)
            print(f"📋 Columnas ({len(schema)}):")
            for _, row in schema.iterrows():
                print(f"  - {row['name']} ({row['type']})")

            # Contar registros
            count = pd.read_sql_query(
                "SELECT COUNT(*) as total FROM comparacion_metricas", conn
            )
            total_records = count["total"].iloc[0]
            print(f"\n📊 Total registros: {total_records}")

            if total_records > 0:
                # Mostrar primeros registros
                sample = pd.read_sql_query(
                    "SELECT * FROM comparacion_metricas LIMIT 5", conn
                )
                print("\n📄 PRIMEROS 5 REGISTROS:")
                print("-" * 80)
                print(sample.to_string())

                # Verificar valores no-cero
                non_zero_checks = {
                    "s1_tiempo_actual > 0": "SELECT COUNT(*) as count FROM comparacion_metricas WHERE s1_tiempo_actual > 0",
                    "s2_tiempo_actual > 0": "SELECT COUNT(*) as count FROM comparacion_metricas WHERE s2_tiempo_actual > 0",
                    "s1_vehiculos_actual > 0": "SELECT COUNT(*) as count FROM comparacion_metricas WHERE s1_vehiculos_actual > 0",
                    "s2_vehiculos_actual > 0": "SELECT COUNT(*) as count FROM comparacion_metricas WHERE s2_vehiculos_actual > 0",
                }

                print("\n📈 VERIFICACIÓN DE DATOS NO-CERO:")
                for condition, query in non_zero_checks.items():
                    try:
                        result = pd.read_sql_query(query, conn)
                        count = result["count"].iloc[0]
                        percentage = (
                            (count / total_records) * 100 if total_records > 0 else 0
                        )
                        status = "✅" if count > 0 else "❌"
                        print(
                            f"  {status} {condition}: {count}/{total_records} ({percentage:.1f}%)"
                        )
                    except Exception as e:
                        print(f"  ❌ Error en {condition}: {e}")

                # Rangos de valores
                try:
                    ranges_query = """
                        SELECT
                            MIN(s1_tiempo_actual) as s1_tiempo_min, MAX(s1_tiempo_actual) as s1_tiempo_max,
                            MIN(s2_tiempo_actual) as s2_tiempo_min, MAX(s2_tiempo_actual) as s2_tiempo_max,
                            MIN(s1_vehiculos_actual) as s1_veh_min, MAX(s1_vehiculos_actual) as s1_veh_max,
                            MIN(s2_vehiculos_actual) as s2_veh_min, MAX(s2_vehiculos_actual) as s2_veh_max,
                            AVG(s1_tiempo_actual) as s1_tiempo_avg, AVG(s2_tiempo_actual) as s2_tiempo_avg
                        FROM comparacion_metricas
                    """
                    ranges = pd.read_sql_query(ranges_query, conn)
                    print("\n📊 RANGOS Y PROMEDIOS DE VALORES:")
                    print("-" * 50)

                    for col in ranges.columns:
                        value = ranges[col].iloc[0]
                        if value is not None:
                            print(f"  {col}: {value:.2f}")
                        else:
                            print(f"  {col}: NULL")

                except Exception as e:
                    print(f"❌ Error calculando rangos: {e}")

                # Verificar timestamps
                try:
                    timestamp_info = pd.read_sql_query(
                        """
                        SELECT
                            MIN(timestamp_simulacion) as min_ts,
                            MAX(timestamp_simulacion) as max_ts,
                            COUNT(DISTINCT timestamp_simulacion) as unique_timestamps
                        FROM comparacion_metricas
                    """,
                        conn,
                    )

                    print("\n🕐 INFORMACIÓN DE TIMESTAMPS:")
                    print(f"  Timestamp mínimo: {timestamp_info['min_ts'].iloc[0]}")
                    print(f"  Timestamp máximo: {timestamp_info['max_ts'].iloc[0]}")
                    print(
                        f"  Timestamps únicos: {timestamp_info['unique_timestamps'].iloc[0]}"
                    )

                except Exception as e:
                    print(f"❌ Error analizando timestamps: {e}")
            else:
                print("⚠️ La tabla existe pero está VACÍA")
        else:
            print("\n❌ Tabla 'comparacion_metricas' NO ENCONTRADA")

        # 3. Analizar tabla de resúmenes
        if "comparacion_resumenes" in tables["name"].values:
            print("\n" + "=" * 50)
            print("🔍 ANÁLISIS DE 'comparacion_resumenes'")
            print("=" * 50)

            summary_count = pd.read_sql_query(
                "SELECT COUNT(*) as total FROM comparacion_resumenes", conn
            )
            total_summaries = summary_count["total"].iloc[0]
            print(f"📊 Registros de resumen: {total_summaries}")

            if total_summaries > 0:
                summary = pd.read_sql_query("SELECT * FROM comparacion_resumenes", conn)
                print("\n📄 DATOS DEL RESUMEN:")
                print("-" * 80)
                print(summary.to_string())

                # Verificar si hay valores reales en el resumen
                s1_tiempo = (
                    summary.get("s1_tiempo_promedio_total", pd.Series([0])).iloc[0]
                    if not summary.empty
                    else 0
                )
                s2_tiempo = (
                    summary.get("s2_tiempo_promedio_total", pd.Series([0])).iloc[0]
                    if not summary.empty
                    else 0
                )

                print("\n🎯 VERIFICACIÓN RÁPIDA:")
                print(f"  S1 tiempo promedio total: {s1_tiempo}")
                print(f"  S2 tiempo promedio total: {s2_tiempo}")

                if s1_tiempo > 0 or s2_tiempo > 0:
                    print("  ✅ Hay datos reales en el resumen")
                else:
                    print("  ❌ Los datos del resumen también están en cero")
            else:
                print("⚠️ La tabla existe pero está VACÍA")
        else:
            print("\n❌ Tabla 'comparacion_resumenes' NO ENCONTRADA")

        conn.close()

        # 4. Diagnóstico y recomendaciones
        print("\n" + "=" * 60)
        print("🎯 DIAGNÓSTICO Y RECOMENDACIONES")
        print("=" * 60)

        if "comparacion_metricas" not in tables["name"].values:
            print("❌ PROBLEMA: Tabla principal no existe")
            print(
                "💡 SOLUCIÓN: Regenerar la base de datos ejecutando una nueva simulación"
            )
        elif total_records == 0:
            print("❌ PROBLEMA: Tabla existe pero está vacía")
            print("💡 SOLUCIÓN: Verificar que ComparisonLogger esté funcionando")
        else:
            # Verificar si hay datos no-cero
            has_real_data = False
            try:
                for condition, query in non_zero_checks.items():
                    result = pd.read_sql_query(query, conn)
                    if result["count"].iloc[0] > 0:
                        has_real_data = True
                        break
            except:
                pass

            if has_real_data:
                print("✅ PROBLEMA: Los datos existen y tienen valores reales")
                print(
                    "💡 SOLUCIÓN: El problema está en el frontend - revisar consultas SQL"
                )
            else:
                print("❌ PROBLEMA: Los datos existen pero todos son ceros")
                print(
                    "💡 SOLUCIÓN: El problema está en ComparisonLogger - no recibe datos reales"
                )

    except sqlite3.Error as e:
        print(f"❌ Error de base de datos: {e}")
    except Exception as e:
        print(f"❌ Error general: {e}")


if __name__ == "__main__":
    diagnose_comparison_db()
