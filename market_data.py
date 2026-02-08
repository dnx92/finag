import requests
import cachetools.func

class MarketData:
    BASE_URL = "https://dolarapi.com/v1/dolares"

    @staticmethod
    @cachetools.func.ttl_cache(maxsize=10, ttl=300) # Cache por 5 minutos
    def get_dolar_rates():
        """
        Obtiene las cotizaciones del dólar (Oficial, Blue, MEP, CCL, Tarjeta)
        desde DolarApi.com. Retorna una lista de diccionarios.
        """
        try:
            response = requests.get(MarketData.BASE_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Filtramos y ordenamos lo que nos interesa
            tipos_interes = ['oficial', 'blue', 'bolsa', 'contadoconliqui', 'tarjeta']
            filtered_data = [d for d in data if d['casa'] in tipos_interes]
            
            # Mapeo de nombres amigables
            nombres = {
                'oficial': 'Oficial',
                'blue': 'Blue',
                'bolsa': 'MEP',
                'contadoconliqui': 'CCL',
                'tarjeta': 'Tarjeta'
            }
            
            results = []
            for item in filtered_data:
                results.append({
                    'nombre': nombres.get(item['casa'], item['nombre']),
                    'compra': item['compra'],
                    'venta': item['venta'],
                    'fecha': item['fechaActualizacion']
                })
                
            return results
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return []

    @staticmethod
    @cachetools.func.ttl_cache(maxsize=10, ttl=3600) # Cache por 1 hora
    def get_economic_indicators():
        """
        Obtiene indicadores económicos (UVA, CER, Plazo Fijo, Badlar) 
        desde ArgentinaDatos API.
        """
        indicators = {
            "tna_pf": {"nombre": "Plazo Fijo (TNA)", "valor": "N/A", "fecha": "-"},
            "cer": {"nombre": "CER", "valor": "N/A", "fecha": "-"},
            "uva": {"nombre": "UVA", "valor": "N/A", "fecha": "-"},
            "badlar": {"nombre": "Badlar", "valor": "N/A", "fecha": "-"},
            "caucion": {"nombre": "Caución (Est.)", "valor": "32.5%", "fecha": "Est."}, # Placeholder
            "tamar": {"nombre": "Tamar", "valor": "N/A", "fecha": "-"}
        }

        # Helper para hacer requests seguros (o inseguros si falla SSL)
        def fetch_api(url):
            try:
                # Intentamos verificar SSL, si falla, intentamos sin verificar (hack para ArgentinaDatos)
                try:
                    resp = requests.get(url, timeout=3)
                except requests.exceptions.SSLError:
                    resp = requests.get(url, timeout=3, verify=False)
                
                if resp.status_code == 200:
                    return resp.json()
            except Exception as e:
                print(f"Error fetching {url}: {e}")
            return None

        # 1. Plazo Fijo (TNA) - Usamos una fuente alternativa o hardcodeamos si falla
        # ArgentinaDatos endpoint para plazo fijo
        pf_data = fetch_api("https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo")
        if pf_data and len(pf_data) > 0:
            last = pf_data[-1] # Ultimo valor
            indicators["tna_pf"] = {"nombre": "Plazo Fijo (TNA)", "valor": f"{last.get('valor', 0)*100:.1f}%", "fecha": last.get('fecha', '-')}

        # 2. UVA
        uva_data = fetch_api("https://api.argentinadatos.com/v1/finanzas/indices/uva")
        if uva_data and len(uva_data) > 0:
            last = uva_data[-1]
            indicators["uva"] = {"nombre": "UVA", "valor": f"${last.get('valor', 0):.2f}", "fecha": last.get('fecha', '-')}
            
        # 3. CER
        cer_data = fetch_api("https://api.argentinadatos.com/v1/finanzas/indices/cer")
        if cer_data and len(cer_data) > 0:
            last = cer_data[-1]
            indicators["cer"] = {"nombre": "CER", "valor": f"{last.get('valor', 0):.2f}", "fecha": last.get('fecha', '-')}

        return indicators
