import pandas as pd
from datetime import datetime, timedelta
import os
import json

class DataManager:
    def __init__(self):
        # Por defecto usamos mock para evitar errores de credenciales al inicio
        self.use_mock = True
        # Aquí se podría implementar la lógica para cargar credenciales de un .json si existe
        if os.path.exists("credentials.json"):
            self.use_mock = False

    def _get_mock_finanzas(self):
        data = {
            "Fecha": [datetime.now().date() - timedelta(days=i*10) for i in range(5)],
            "Instrumento": ["LECAP S31G6", "ON YPF", "TAMAR", "LECAP S31G6", "CEDEAR SPY"],
            "Capital": [1000000.0, 5000000.0, 250000.0, 1500000.0, 3000000.0],
            "Tasa": [0.45, 0.08, 0.52, 0.44, 0.0], # TNA o Yield
            "Vencimiento": [
                datetime.now().date() + timedelta(days=2), 
                datetime.now().date() + timedelta(days=180),
                datetime.now().date() + timedelta(days=45),
                datetime.now().date() + timedelta(days=2),
                datetime.now().date() + timedelta(days=365)
            ],
            "Estado": ["Activo", "Activo", "Activo", "Activo", "Activo"],
            "Moneda": ["ARS", "USD", "ARS", "ARS", "USD"]
        }
        return pd.DataFrame(data)

    def _get_mock_propiedades(self):
        data = {
            "Nombre": ["Estancia La Paz", "Campo Norte", "Lote 4"],
            "Latitud": [-34.6037, -31.4201, -32.9442],
            "Longitud": [-58.3816, -64.1888, -60.6505],
            "Superficie": [500, 250, 100],
            "Tipo": ["Yerba", "Vacío", "Madera"],
            "Valor de Compra": [1500000, 800000, 400000],
            "Estado de Arrendamiento": ["Propio", "Arrendado", "Propio"]
        }
        return pd.DataFrame(data)

    def _get_mock_inventario(self):
        data = {
            "Ubicación": ["Estancia La Paz", "Estancia La Paz", "Campo Norte"],
            "Item": ["Tractor John Deere", "Semillas Soja", "Fertilizante"],
            "Cantidad": [2, 5000, 2000],
            "Fecha de Compra": ["2023-01-15", "2024-02-10", "2024-03-01"],
            "Estado": ["Operativo", "En Stock", "En Stock"]
        }
        return pd.DataFrame(data)

    def _get_mock_vencimientos(self):
        data = {
            "Tarea": ["Reinversión LECAP", "Pago Arrendamiento", "Vacunación Ganado", "Venta Cosecha"],
            "Fecha Límite": [
                datetime.now().date() + timedelta(days=2),
                datetime.now().date() + timedelta(days=15),
                datetime.now().date() + timedelta(days=5),
                datetime.now().date() + timedelta(days=30)
            ],
            "Prioridad": ["Alta", "Alta", "Media", "Media"],
            "Estado": ["Pendiente", "Pendiente", "Pendiente", "Pendiente"]
        }
        return pd.DataFrame(data)

    def get_data(self, sheet_name):
        if self.use_mock:
            if sheet_name == "Finanzas": return self._get_mock_finanzas()
            if sheet_name == "Propiedades": return self._get_mock_propiedades()
            if sheet_name == "Inventario": return self._get_mock_inventario()
            if sheet_name == "Vencimientos": return self._get_mock_vencimientos()
            return pd.DataFrame()
        
        # Aquí iría la lógica real de gspread si no fuera mock
        # Por ahora mantenemos el mock como default robusto
        print(f"Advertencia: Intentando leer {sheet_name} sin configuración real. Usando Mock.")
        return self.get_data("Finanzas") # Fallback dummy
