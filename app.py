import streamlit as st
import pandas as pd
import os

# Importamos con los nombres EXACTOS de tus archivos en GitHub
from scraper_mercadona import ejecutar_mercadona
from scraper_carrefour import ejecutar_carrefour
from scraper_aldi import ejecutar_aldi

st.set_page_config(page_title="Sherlock Supermercados", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ Sherlock Holmes: Análisis de Proximidad")

st.sidebar.header("Panel de Extracción")
supermercado = st.sidebar.selectbox("Selecciona Supermercado", ["Mercadona", "Carrefour", "Aldi"])

if st.sidebar.button("🚀 Ejecutar Análisis"):
    with st.spinner(f"Analizando {supermercado}..."):
        if supermercado == "Mercadona":
            df = ejecutar_mercadona()
        elif supermercado == "Carrefour":
            df = ejecutar_carrefour()
        else:
            df = ejecutar_aldi()

        if not df.empty:
            if 'Es_Respaldo' in df.columns:
                st.warning("⚠️ Mostrando datos guardados de la última auditoría.")
                df = df.drop(columns=['Es_Respaldo'])
            else:
                st.success("✅ Extracción en tiempo real completada.")

            st.dataframe(df, use_container_width=True)
        else:
            st.error("No se pudieron obtener datos.")


# Pie de página
st.sidebar.markdown("---")
st.sidebar.caption("v1.1.0 | Sherlock Holmes Supermercados")
st.sidebar.caption("🚀 Desarrollado por: Alejando Sanchez y Andrew Villamar")
st.sidebar.caption("Proyecto de Ciencia de Datos e Intelgencia Artificial, para la asigantura de ALN - 2026")