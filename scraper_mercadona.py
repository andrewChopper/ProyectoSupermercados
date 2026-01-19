# El de Alex, adaptado a una función pero con la última función de el de gemini


# El de Alex pero adaptado a una función

import requests
import pandas as pd
import time
import random
import re

# --- 1. CONFIGURACIÓN ---
ZIP_CODE = "46002"
CANTIDAD_POR_CATEGORIA = 20

CATEGORIAS_OBJETIVO = {
    27:  "Fruta",
    29:  "Verdura",
    38:  "Carne (Aves)",
    31:  "Pescado Fresco",
    121: "Legumbres",
    148: "Congelados (Carne)"
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'x-customer-zipcode': ZIP_CODE
}

# --- 3. ANALIZADOR PROFUNDO ACTUALIZADO ---
def analizar_texto_profundo(texto_completo):
    """
    Busca pistas de origen en un texto largo usando patrones comunes de supermercado.
    """
    if not texto_completo: return None
    texto = texto_completo.lower()

    # 1. Búsqueda de Códigos de Pesca (FAO) - Típico en Pescado
    # Busca "FAO" seguido de números (ej. FAO 27)
    match_fao = re.search(r'(fao\s*\d+[\.\d]*)', texto)
    if match_fao:
        return f"Zona {match_fao.group(1).upper()}"

    # 2. Palabras clave de origen animal/vegetal
    # Busca frases como "Criado en España", "Origen: Marruecos", "Cultivado en Perú"
    keywords = ["origen", "cultivado en", "criado en", "sacrificado en", "país de cría", "procedencia", "elaborado en"]

    for key in keywords:
        if key in texto:
            # Intentamos extraer lo que viene después de la palabra clave
            # Regex: Busca la keyword + dos puntos opcionales + el texto siguiente hasta un punto o coma
            patron = rf"{key}[:\s]+([^.,;]+)"
            match = re.search(patron, texto)
            if match:
                clean_match = match.group(1).strip().title()
                # Filtro: Si el resultado es muy largo (>30 chars) probablemente cogimos basura, lo descartamos
                if len(clean_match) < 40:
                    return clean_match

    # 3. Búsqueda bruta de países comunes (Último recurso)
    paises = ["españa", "spain", "marruecos", "perú", "argentina", "chile", "sudáfrica", "portugal", "francia", "noruega", "china", "canadá", "usa", "eeuu"]
    encontrados = [p.title() for p in paises if p in texto]
    if encontrados:
        return "/".join(list(set(encontrados))) + " (Detectado en texto)"

    return None

# --- 4. FUNCIONES DE API ---
def recolectar_ids_recursivo(data_json, lista_ids):
    if isinstance(data_json, dict):
        if 'products' in data_json and data_json['products']:
            for p in data_json['products']:
                lista_ids.append(p['id'])
        if 'categories' in data_json and data_json['categories']:
            for subcat in data_json['categories']:
                recolectar_ids_recursivo(subcat, lista_ids)

def obtener_detalle_producto(id_prod):
    try:
        url = f"https://tienda.mercadona.es/api/products/{id_prod}"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            time.sleep(5)
    except:
        pass
    return None

# --- FUNCIÓN PRINCIPAL PARA EL FRONTEND ---
def ejecutar_mercadona():
    """
    Función que ejecuta la extracción completa y devuelve un DataFrame.
    """
    datos_totales = []

    for cat_id, nombre_cat in CATEGORIAS_OBJETIVO.items():
        try:
            resp = requests.get(f"https://tienda.mercadona.es/api/categories/{cat_id}", headers=HEADERS)
            if resp.status_code != 200: continue

            ids = []
            recolectar_ids_recursivo(resp.json(), ids)
            ids = list(set(ids))[:CANTIDAD_POR_CATEGORIA]

            for i, prod_id in enumerate(ids):
                data = obtener_detalle_producto(prod_id)

                if data:
                    info_legal = data.get('price_instructions', {}).get('legal_text', '') or ""
                    detalles = data.get('details', {})
                    descripcion = detalles.get('description', '') or ""
                    uso = detalles.get('usage_instructions', '') or ""

                    texto_gigante = f"{info_legal} {descripcion} {uso}"

                    # Lógica de Origen
                    origen = data.get('origin') or detalles.get('origin')
                    if not origen:
                        origen = analizar_texto_profundo(texto_gigante)

                    # Proveedor
                    proveedor = "Desconocido"
                    supp = detalles.get('suppliers')
                    if supp and len(supp) > 0:
                        proveedor = supp[0].get('name')

                    # Precio y Unidad (campos necesarios para el FrontEnd)
                    precio = data.get('price_instructions', {}).get('unit_price', 0)
                    unidad = data.get('price_instructions', {}).get('unit_name', '-')

                    datos_totales.append({
                        'Categoría': nombre_cat,
                        'Producto': data.get('display_name'),
                        'Origen': origen if origen else "Desconocido",
                        'Proveedor': proveedor,
                        'Precio': f"{precio} €",
                        'Unidad': unidad
                    })

                # Pausa para evitar bloqueos
                time.sleep(random.uniform(0.1, 0.3))

        except Exception as e:
            print(f"Error en categoría {nombre_cat}: {e}")

    if datos_totales:
        return pd.DataFrame(datos_totales).fillna("-")
    else:
        return pd.DataFrame()
