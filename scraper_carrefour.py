from curl_cffi import requests
import pandas as pd
import time
import random
import re
import os

# --- 1. CONFIGURACIÓN (Actualizada con tu último curl) ---
URL_API = "https://www.carrefour.es/search-api/query/v1/search"
CANTIDAD_POR_CATEGORIA = 40

CATEGORIAS_OBJETIVO = {
    "Fruta": "fruta",
    "Verdura": "verdura",
    "Carne (Aves)": "pollo",
    "Pescado Fresco": "pescado fresco",
    "Legumbres": "legumbres",
    "Congelados (Carne)": "carne congelada"
}

BASE_PARAMS = {
    'internal': 'true',
    'instance': 'x-carrefour',
    'env': 'https://www.carrefour.es',
    'scope': 'desktop',
    'lang': 'es',
    'session': 'empathy',
    'citrusCatalog': 'home',
    'baseUrlCitrus': 'https://www.carrefour.es',
    'enabled': 'true',
    'store': '005290',
    'shopperId': '38TODjYTJKBuHYGKDY9fiiNQV48',
    'hasConsent': 'false',
    'siteKey': 'wFOzqveg',
    'origin': 'search_box:none',
    'start': '0',
    'rows': str(CANTIDAD_POR_CATEGORIA)
}

HEADERS = {
    'accept': '*/*',
    'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
    'referer': 'https://www.carrefour.es/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'x-origin': 'https://www.carrefour.es',
    'Cookie': '_cfuvid=d8EJgeKBjVSMsEO5daXDPwnWzhz0CtxB1DIapad5y7M-1768808559501-0.0.1.1-604800000; salepoint=005290||28232|A_DOMICILIO|0; session_id=38TODjYTJKBuHYGKDY9fiiNQV48; __cf_bm=8Rv5nr3k4aUevf7GJPOvY76v5v4QM8x5Y9q9.dikfIY-1768819976-1.0.1.1-3i2zncMVRK8TN3Sn8UsMnLn_1_C.pmvu8BxHkmOId0R1Rcs0XAUVZHionB82aX1GUw3kIOaP7Sb_dYvjYH.VXNrq9k5721jw9Tak_XCkH0I; cf_clearance=pzpDU8mRRwaZde4g.tpz9RstxGH6SPQhn.aGY3CqgeU-1768819977-1.2.1.1-j2eyc.01k.RZonfWzCv8JMqmaWSRT.4UqF4ejt3x62xX9_HobA6d9D5JMg_ncoPY46uFwX1KkiUcE3SIaW7EU2JYvIJZXBSnO5AOhxqc3zoQEW.p39_9kZqSOC.uKd1zT1hbFVftwpSYSFReeCeJkQVaFbjscfTVgGPjHS2hiRrRRcoAfAVoQO_LubpAlly46sodnHUNdHPYwlpqNC_0a8aaJGaud1Vb87wQyFt2vUk;'
}

# --- 2. DETECTIVE INTERNACIONAL ---
def analizar_origen_carrefour(item):
    nombre = item.get('display_name', '').upper()
    marca = item.get('brand', '').upper()
    ean = str(item.get('ean13', ''))
    texto_completo = f"{nombre} {marca}"

    ean_map = {
        '84': 'España', ('30','31','32','33','34','35','36','37'): 'Francia',
        '560': 'Portugal', ('80','81','82','83'): 'Italia', '611': 'Marruecos',
        '775': 'Perú', '87': 'Países Bajos', '779': 'Argentina', '780': 'Chile'
    }

    for prefix, country in ean_map.items():
        if ean.startswith(prefix): return country

    if any(k in texto_completo for k in ["ESPAÑA", "NACIONAL", "CANARIAS"]): return "España"

    otros_paises = {"PORTUGAL": "Portugal", "ITALIA": "Italia", "MARRUECOS": "Marruecos", "PERÚ": "Perú", "SUDÁFRICA": "Sudáfrica"}
    for key, val in otros_paises.items():
        if key in texto_completo: return val

    marcas_espanolas = ["CENTRAL LECHERA", "PULEVA", "PASCUAL", "KAIKU", "CAMPOFRIO", "EL POZO"]
    if any(m in marca for m in marcas_espanolas) or "CARREFOUR" in marca: return "España"

    return "Desconocido"

# --- 3. FUNCIÓN PRINCIPAL CON FALLBACK ---
def ejecutar_carrefour():
    datos_totales = []
    # ACTUALIZADO EL NOMBRE DEL ARCHIVO DE RESPALDO
    archivo_respaldo = os.path.join(os.path.dirname(__file__), "analisis_carrefour.csv")

    try:
        for nombre_cat, query_busqueda in CATEGORIAS_OBJETIVO.items():
            params = BASE_PARAMS.copy()
            params['query'] = query_busqueda
            resp = requests.get(URL_API, headers=HEADERS, params=params, impersonate="chrome124")

            if resp.status_code == 200:
                productos = resp.json().get('content', {}).get('docs', [])
                for p in productos:
                    datos_totales.append({
                        'Categoría': nombre_cat,
                        'Producto': p.get('display_name', 'Sin nombre'),
                        'Origen': analizar_origen_carrefour(p),
                        'Proveedor': p.get('brand', 'Desconocido'),
                        'Precio': f"{p.get('active_price', 0)} €",
                        'Unidad': p.get('price_per_unit_text', '-')
                    })
                time.sleep(0.3)
            else:
                raise Exception(f"Sesión caducada ({resp.status_code})")

        return pd.DataFrame(datos_totales)

    except Exception as e:
        print(f"Scraping fallido ({e}). Intentando cargar {archivo_respaldo}")
        if os.path.exists(archivo_respaldo):
            df = pd.read_csv(archivo_respaldo)
            df['Es_Respaldo'] = True
            return df
        return pd.DataFrame(columns=['Categoría', 'Producto', 'Origen', 'Proveedor', 'Precio', 'Unidad'])