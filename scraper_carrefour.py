from curl_cffi import requests
import pandas as pd
import time
import random
import re

# --- 1. CONFIGURACIÓN ---
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
    'shopperId': '38T14zNQXO9omcOsKpNqy5dEb3H',
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
    'Cookie': 'session_id=38T14zNQXO9omcOsKpNqy5dEb3H; __cf_bm=H6zIWDGNG5LN6XA_0F1b3fEt2k7nW.tqkzJezCqBceI-1768808559-1.0.1.1-8PBoWVt_RzRdAamLDdFmzVScu7ZTRtq.IVpwjNVZ9xvwzcomvFsqdZqlqE3sOvbwoeVvMU3WyeaDOxkEwNwOsFQKwTWaVFiMxjUNVdEvLUs; _cfuvid=d8EJgeKBjVSMsEO5daXDPwnWzhz0CtxB1DIapad5y7M-1768808559501-0.0.1.1-604800000; salepoint=005290||28232|A_DOMICILIO|0; cf_clearance=wRkU3iYKIQzUB3ETJbViT3zmn_mxOG0ylqFe.YvwI1E-1768808560-1.2.1.1-cSJB_KZ2UMTtxPonYXHCsVt56UI0I5VQfXJOs7tW80eCRFPARlt0ez2TbQe4Vclz7DzzKYtE8RsFy1yUpzCHhsdfql8qmlVyu3O5JUDdQrShEDGAt8huHnuTxvB4JsdrI5fatPe_dOvMO7M.V4gpA0YQMjRkmdIHO0AG_1FJcou3EdkIsn.BcqkCeZLJWgnazgTRGgMFQ.aPRxKPH4NGtoFopc.zAE8YCrmn27PAmMo; _uetsid=70a500c0f50a11f0af25c305854856ed; _uetvid=70a54260f50a11f0be8cbbe9e6eac694; OptanonAlertBoxClosed=2026-01-19T07:42:44.937Z; eupubconsent-v2=CQeRftgQeRftgAcABBESCOFgAAAAAAAAAChQAAAAAAAA.YAAAAAAAAAAA.ILewBQAKgAYABkAS0C3o; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Jan+19+2026+08%3A42%3A45+GMT%2B0100+(hora+est%C3%A1ndar+de+Europa+central)&version=202510.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=6e84a1c2-a6f9-4a5e-9d06-01e355ef7981&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0022%3A0%2CC0166%3A0%2CC0096%3A0%2CC0021%3A0%2CC0007%3A0%2CC0052%3A0%2CC0002%3A1%2CC0003%3A1%2CC0001%3A1%2CC0063%3A0%2CC0174%3A0%2CC0081%3A0%2CC0054%3A0%2CC0051%3A0%2CC0023%3A0%2CC0025%3A0%2CC0038%3A0%2CC0041%3A0%2CC0040%3A0%2CC0057%3A0%2CC0082%3A0%2CC0135%3A0%2CC0141%3A0%2CC0180%3A0%2CC0084%3A0%2CC0032%3A0%2CC0039%3A0%2CC0004%3A0%2CV2STACK42%3A0&intType=2; OneTrustGroupsConsent-ES=,C0002,C0003,C0001,'
}

# --- 2. DETECTIVE ---
def analizar_origen_carrefour(item):
    nombre = item.get('display_name', '').upper()
    marca = item.get('brand', '').upper()
    ean = str(item.get('ean13', ''))
    texto_completo = f"{nombre} {marca}"

    if ean.startswith('84'): return "España"
    if ean.startswith(('30','31','32','33','34','35','36','37')): return "Francia"
    if "ESPAÑA" in texto_completo or "NACIONAL" in texto_completo: return "España"
    if "CANARIAS" in texto_completo: return "España"

    marcas_espanolas = ["CENTRAL LECHERA", "PULEVA", "PASCUAL", "KAIKU", "LAUKI", "RIO", "CELTA", "POZO", "CAMPOFRIO", "GALLO", "EL POZO"]
    if any(m in marca for m in marcas_espanolas): return "España"
    if "CARREFOUR" in marca: return "España"

    return "Desconocido"

# --- 3. FUNCIÓN PRINCIPAL ---
def ejecutar_carrefour():
    datos_totales = []

    for nombre_cat, query_busqueda in CATEGORIAS_OBJETIVO.items():
        params = BASE_PARAMS.copy()
        params['query'] = query_busqueda

        try:
            resp = requests.get(URL_API, headers=HEADERS, params=params, impersonate="chrome124")

            if resp.status_code == 200:
                data = resp.json()
                productos = data.get('content', {}).get('docs', [])

                for p in productos:
                    datos_totales.append({
                        'Categoría': nombre_cat,
                        'Producto': p.get('display_name', 'Sin nombre'),
                        'Origen': analizar_origen_carrefour(p),
                        'Proveedor': p.get('brand', 'Desconocido'),
                        'Precio': f"{p.get('active_price', 0)} €",
                        'Unidad': p.get('price_per_unit_text', '-')
                    })

                time.sleep(random.uniform(0.3, 0.6))
        except Exception as e:
            print(f"Error en Carrefour: {e}")

    return pd.DataFrame(datos_totales).fillna("-")