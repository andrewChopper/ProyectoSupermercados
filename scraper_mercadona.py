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

# --- 2. FUNCIÓN DE LIMPIEZA MAESTRA ---
def estandarizar_pais(texto):
    """
    Elimina ruidos como 'origen: ', 'cultivado en' y unifica mayúsculas/minúsculas.
    """
    if not texto: return "Desconocido"

    # Eliminamos etiquetas comunes (Case Insensitive)
    ruido = ["origen:", "cultivado en", "procedencia:", "españa - elaborado en", "elaborado en"]
    texto_limpio = str(texto).lower()
    for r in ruido:
        texto_limpio = texto_limpio.replace(r, "")

    # Normalizamos a formato Título: "ESPAÑA" -> "España"
    texto_limpio = texto_limpio.strip().title()

    # Correcciones finales
    mapeo = {"Espana": "España", "Spain": "España", "None": "Desconocido"}
    return mapeo.get(texto_limpio, texto_limpio)

# --- 3. ANALIZADOR PROFUNDO ACTUALIZADO ---
def analizar_texto_profundo(texto_completo):
    if not texto_completo: return None
    texto = texto_completo.lower()

    # FAO (Pescado)
    match_fao = re.search(r'(fao\s*\d+[\.\d]*)', texto)
    if match_fao:
        return f"Zona {match_fao.group(1).upper()}"

    # Keywords con Regex mejorada
    keywords = ["origen", "cultivado en", "criado en", "sacrificado en", "procedencia", "elaborado en"]
    for key in keywords:
        if key in texto:
            patron = rf"{key}[:\s]+([^.,;]+)"
            match = re.search(patron, texto)
            if match:
                res = match.group(1).strip()
                if len(res) < 30: return res

    # Detección Internacional (Ampliamos países)
    paises = ["españa", "spain", "marruecos", "perú", "argentina", "chile", "sudáfrica", "portugal", "francia", "italia"]
    encontrados = [p.title() for p in paises if p in texto]
    if encontrados:
        return encontrados[0] # Devolvemos el primer país detectado

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
        if resp.status_code == 200: return resp.json()
    except: pass
    return None

# --- 5. FUNCIÓN PRINCIPAL PARA EL FRONTEND ---
def ejecutar_mercadona():
    datos_totales = []

    for cat_id, nombre_cat in CATEGORIAS_OBJETIVO.items():
        try:
            resp = requests.get(f"https://tienda.mercadona.es/api/categories/{cat_id}", headers=HEADERS)
            if resp.status_code != 200: continue

            ids = []
            recolectar_ids_recursivo(resp.json(), ids)
            ids = list(set(ids))[:CANTIDAD_POR_CATEGORIA]

            for prod_id in ids:
                data = obtener_detalle_producto(prod_id)
                if data:
                    detalles = data.get('details', {})
                    # Unimos textos para el detective
                    texto_gigante = f"{data.get('price_instructions', {}).get('legal_text', '')} {detalles.get('description', '')}"

                    # Prioridad de Origen
                    origen_raw = data.get('origin') or detalles.get('origin') or analizar_texto_profundo(texto_gigante)

                    # --- APLICAMOS LA LIMPIEZA FINAL ---
                    origen_final = estandarizar_pais(origen_raw)

                    # Proveedor
                    proveedor = "Desconocido"
                    supp = detalles.get('suppliers')
                    if supp: proveedor = supp[0].get('name', 'Desconocido').title()

                    datos_totales.append({
                        'Categoría': nombre_cat,
                        'Producto': data.get('display_name', 'Sin nombre'),
                        'Origen': origen_final,
                        'Proveedor': proveedor,
                        'Precio': f"{data.get('price_instructions', {}).get('unit_price', 0)} €",
                        'Unidad': data.get('price_instructions', {}).get('unit_name', '-')
                    })
                time.sleep(random.uniform(0.1, 0.2)) # Pausa anti-bloqueo

        except Exception as e:
            print(f"Error: {e}")

    return pd.DataFrame(datos_totales)