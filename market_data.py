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
