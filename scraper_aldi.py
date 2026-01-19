import requests
import pandas as pd
import time
import random
import re

# --- 1. CONFIGURACIÓN ---
HEADERS = {
    'x-algolia-application-id': 'L9KNU74IO7',
    'x-algolia-api-key': '19b0e28f08344395447c7bdeea32da58',
    'content-type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}
URL_ALGOLIA = "https://l9knu74io7-dsn.algolia.net/1/indexes/*/queries"
CANTIDAD_POR_CATEGORIA = 40

CATEGORIAS_OBJETIVO = {
    "Fruta": "fruta",
    "Verdura": "verdura",
    "Carne": "pollo pavo cerdo vacuno carne",
    "Pescado": "pescado",
    "Legumbres": "legumbres",
    "Lácteos": "leche queso yogur"
}

PALABRAS_PROHIBIDAS = [
    "exprimidor", "batidora", "broca", "juego de", "toallitas", "crema",
    "corporal", "hidratante", "mascarilla", "champú", "gel", "loción",
    "cápsulas", "café", "chocolate", "galletas", "cosmética", "multisuperficies"
]

# --- 2. DETECTIVE ALDI V2.0 ---
def analizar_texto_profundo_aldi(texto_completo, nombre_producto):
    if not texto_completo: return "Desconocido"
    texto = texto_completo.lower()
    nombre = nombre_producto.lower()

    if "dop" in texto or "ribera del duero" in texto or "rueda" in texto or "rioja" in texto:
        return "España"
    if "leche" in nombre and ("xxl" in nombre or "entera" in nombre or "desnatada" in nombre):
        if "corporal" not in nombre:
            return "España"
    if "nacional" in texto or "españa" in texto or "spain" in texto: return "España"

    match = re.search(r"origen[:\s]+(\w+)", texto)
    if match:
        pais = match.group(1).title()
        if pais not in ["La", "El", "Los", "De", "Vegetal", "Animal"]:
            return pais

    if "el mercado" in texto: return "España"
    if "milsani" in texto: return "Alemania/España"
    if "gutbio" in texto: return "UE/No UE"

    return "Desconocido"

# --- 3. FUNCIÓN PRINCIPAL PARA EL FRONTEND ---
def ejecutar_aldi():
    datos_totales = []

    for nombre_cat, termino_busqueda in CATEGORIAS_OBJETIVO.items():
        try:
            payload = {
                "requests": [{
                    "indexName": "prod_es_es_es_offers",
                    "params": f"query={termino_busqueda}&hitsPerPage={CANTIDAD_POR_CATEGORIA}"
                }]
            }

            resp = requests.post(URL_ALGOLIA, headers=HEADERS, json=payload)
            hits = resp.json()['results'][0]['hits']

            if not hits: continue

            for p in hits:
                nombre = p.get('productName', 'Desconocido')

                # Filtro de limpieza (La Escoba)
                if any(prohibida in nombre.lower() for prohibida in PALABRAS_PROHIBIDAS):
                    continue

                desc = p.get('shortDescription', '') or ""
                marketing = p.get('marketingText', '') or ""
                marca = p.get('brandName', 'Desconocido') or "Desconocido"
                legal = p.get('legalContent', '') or ""

                texto_gigante = f"{desc} {marketing} {legal} {marca} {nombre}"
                origen = analizar_texto_profundo_aldi(texto_gigante, nombre)

                precio = p.get('priceFormatted', 'N/A')
                unidad = p.get('salesUnit', '-')

                datos_totales.append({
                    'Categoría': nombre_cat,
                    'Producto': nombre,
                    'Origen': origen,
                    'Proveedor': marca, # Mapeado a Proveedor para unificar
                    'Precio': precio,
                    'Unidad': unidad
                })

            time.sleep(random.uniform(0.3, 0.6))

        except Exception as e:
            print(f"Error en Aldi: {e}")

    if datos_totales:
        return pd.DataFrame(datos_totales).fillna("-")
    else:
        return pd.DataFrame()