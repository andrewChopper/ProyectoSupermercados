import streamlit as st
import pandas as pd
import os

# Importamos tus motores de búsqueda
from scraper_mercadona import ejecutar_mercadona
from scraper_carrefour import ejecutar_carrefour
from scraper_aldi import ejecutar_aldi

# 1. Configuración de la página
st.set_page_config(page_title="Sherlock Supermercados", page_icon="🕵️‍♂️", layout="wide")

# Estilo personalizado para el título
st.title("🕵️‍♂️ Sherlock Holmes: Análisis de Proximidad")
st.markdown("""
Esta herramienta analiza automáticamente el **origen de los productos frescos** para promover la compra de proximidad y el apoyo a los **agricultores locales**.
""")

# 2. Panel Lateral
st.sidebar.header("Panel de Extracción")
supermercado = st.sidebar.selectbox(
    "Selecciona el supermercado a analizar:",
    ["Mercadona", "Carrefour", "Aldi"]
)

# 3. Ejecución Principal
if st.sidebar.button("🚀 Ejecutar Análisis Completo"):
    st.info(f"Iniciando extracción en **{supermercado}**...")

    with st.spinner("Procesando categorías y analizando orígenes..."):
        try:
            # Llamamos a la función correspondiente
            if supermercado == "Mercadona":
                df_final = ejecutar_mercadona()
            elif supermercado == "Carrefour":
                df_final = ejecutar_carrefour()
            else:
                df_final = ejecutar_aldi()

            # --- GESTIÓN DE RESULTADOS Y RESILIENCIA ---
            if df_final is not None and not df_final.empty:

                # A) Verificamos si los datos son de respaldo (Plan B)
                es_respaldo = False
                if 'Es_Respaldo' in df_final.columns:
                    es_respaldo = True
                    df_final = df_final.drop(columns=['Es_Respaldo']) # Limpiamos la columna de control

                # B) Avisos al usuario según el origen del dato
                if es_respaldo:
                    st.warning(f"⚠️ **Nota:** Los servidores de {supermercado} están protegidos o fuera de servicio. Mostrando datos de la última auditoría guardada.")
                else:
                    st.success(f"✅ Datos de {supermercado} extraídos en tiempo real correctamente.")

                # C) Métricas Visuales
                st.divider()
                m1, m2, m3 = st.columns(3)
                total = len(df_final)
                proximidad = len(df_final[df_final['Origen'] == "España"])
                porcentaje = (proximidad / total) * 100 if total > 0 else 0

                m1.metric("Productos Analizados", total)
                m2.metric("Origen España", proximidad)
                m3.metric("% Proximidad", f"{porcentaje:.1f}%")

                # D) Mostrar Tabla de Datos
                st.subheader("📋 Detalle de Productos Extraídos")
                st.dataframe(df_final, use_container_width=True)

                # E) Botón de Descarga
                csv_data = df_final.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Descargar Reporte CSV",
                    data=csv_data,
                    file_name=f"analisis_{supermercado.lower()}.csv",
                    mime="text/csv"
                )
            else:
                st.error("No se han podido recuperar datos. Revisa la conexión o el estado de la API.")

        except Exception as e:
            st.error(f"Error crítico en el proceso: {e}")

else:
    st.write("👈 Utiliza el panel lateral para seleccionar un supermercado y comenzar la extracción.")

# Pie de página
st.sidebar.markdown("---")
st.sidebar.caption("v1.1.0 | Sherlock Holmes Supermercados")
st.sidebar.caption("🚀 Desarrollado por: Alejando Sanchez y Andrew Villamar")
st.sidebar.caption("Proyecto de Ciencia de Datos e Intelgencia Artificial, para la asigantura de ALN - 2026")
