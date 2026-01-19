import streamlit as st
import pandas as pd
# Importamos tus tres motores de búsqueda
from scraper_mercadona import ejecutar_mercadona
from scraper_carrefour import ejecutar_carrefour
from scraper_aldi import ejecutar_aldi

# Configuración estética de la página
st.set_page_config(page_title="Super Sherlock v1.0", page_icon="🕵️‍♂️", layout="wide")

st.title("🕵️‍♂️ Sherlock Holmes: Análisis de Proximidad")
st.markdown("Selecciona un supermercado para extraer los datos de origen de los productos frescos.")

# --- BARRA LATERAL ---
st.sidebar.header("Panel de Extracción")
super_seleccionado = st.sidebar.selectbox(
    "Supermercado a analizar",
    ["Mercadona", "Carrefour", "Aldi"]
)

# Botón principal
if st.sidebar.button("🚀 Ejecutar Extracción Completa"):
    st.info(f"Iniciando extracción en **{super_seleccionado}**... esto puede tardar unos segundos.")

    # Marcador de progreso (Spinner)
    with st.spinner("Analizando categorías y detectando orígenes..."):
        try:
            # Ejecutamos el motor correspondiente
            if super_seleccionado == "Mercadona":
                df_final = ejecutar_mercadona()
            elif super_seleccionado == "Carrefour":
                df_final = ejecutar_carrefour()
            else:
                df_final = ejecutar_aldi()

            # --- MOSTRAR RESULTADOS ---
            st.success(f"¡Extracción de {super_seleccionado} completada con éxito!")

            # Métricas rápidas
            col1, col2 = st.columns(2)
            total_prods = len(df_final)
            proximidad = len(df_final[df_final['Origen'] == "España"])

            col1.metric("Productos Analizados", total_prods)
            col2.metric("Productos de Proximidad (España)", proximidad)

            # Mostrar el Dataframe con estilo
            st.subheader("📋 Datos Extraídos")
            st.dataframe(
                df_final.style.set_properties(**{'background-color': '#f9f9f9', 'color': 'black'}),
                use_container_width=True
            )

            # Botón para descargar el CSV generado desde la web
            csv = df_final.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Descargar CSV de resultados",
                data=csv,
                file_name=f"sherlock_{super_seleccionado.lower()}.csv",
                mime="text/csv",
            )

        except Exception as e:
            st.error(f"Error crítico en la extracción: {e}")
            st.warning("Asegúrate de que las cookies en el script de Carrefour sigan siendo válidas.")

else:
    st.write("👈 Selecciona un supermercado en el menú lateral y pulsa el botón para empezar.")

# Pie de página técnico para tu informe
st.sidebar.markdown("---")
st.sidebar.caption("v1.0.1 | Tecnología: Python + Streamlit + curl_cffi")