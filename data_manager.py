import pandas as pd
from datetime import datetime, timedelta
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import cachetools.func

class DataManager:
    def __init__(self):
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds_file = 'credentials.json'
        self.sheet_name = "memoria monto en pesos tasa y fecha agro-finance" 
        self.client = None
        self.sheet = None
        self.use_mock = True
        
        self._authenticate()

    def _authenticate(self):
        if os.path.exists(self.creds_file):
            try:
                self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, self.scope)
                self.client = gspread.authorize(self.creds)
                
                # Intentamos conectar a la hoja para validar
                try:
                    self.sheet = self.client.open(self.sheet_name)
                    self.use_mock = False
                    print(f"✅ Conectado exitosamente a Google Sheet: {self.sheet_name}")
                except gspread.SpreadsheetNotFound:
                    print(f"⚠️ No se encontró la hoja '{self.sheet_name}'. Asegúrate de compartirla con el bot o cambiar el nombre.")
                    self.use_mock = True
                except Exception as e:
                     print(f"⚠️ Error al abrir la hoja: {e}")
                     self.use_mock = True
            except Exception as e:
                print(f"❌ Error de autenticación con Google: {e}")
                self.use_mock = True
        else:
            print("ℹ️ No se encontró credentials.json, usando Mock Data.")
            self.use_mock = True

    @cachetools.func.ttl_cache(maxsize=10, ttl=60) # Cache de 1 min para no saturar APIs
    def get_data(self, sheet_tab):
        if self.use_mock:
            return self._get_mock_data(sheet_tab)
        
        try:
            worksheet = self.sheet.worksheet(sheet_tab)
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except gspread.WorksheetNotFound:
            print(f"⚠️ Pestaña '{sheet_tab}' no encontrada. Usando Mock.")
            return self._get_mock_data(sheet_tab)
        except Exception as e:
            print(f"Error leyendo {sheet_tab}: {e}")
            return self._get_mock_data(sheet_tab)

    def get_user_config(self, user_id):
        """Obtiene la configuración financiera del usuario (Capital, Tasa, Timestamp)"""
        default_config = {"capital": 0, "rate": 0, "timestamp": datetime.now().isoformat()}
        
        if self.use_mock:
            return default_config

        try:
            ws = self.sheet.worksheet("Usuarios")
            # Buscamos el ID del usuario en la columna 1
            cell = ws.find(user_id)
            if cell:
                row_values = ws.row_values(cell.row)
                # Asumimos orden: ID, Capital, Tasa, Timestamp
                return {
                    "capital": float(row_values[1]) if len(row_values) > 1 else 0,
                    "rate": float(row_values[2]) if len(row_values) > 2 else 0,
                    "timestamp": row_values[3] if len(row_values) > 3 else datetime.now().isoformat()
                }
            return default_config
        except Exception as e:
            print(f"Error fetching user config: {e}")
            return default_config

    def save_user_config(self, user_id, capital, rate):
        """Guarda la configuración financiera del usuario"""
        if self.use_mock:
            print(f"Mock Save: {user_id} -> ${capital} @ {rate}%")
            return True

        try:
            ws = self.sheet.worksheet("Usuarios")
            timestamp = datetime.now().isoformat()
            
            # Buscamos si el usuario ya existe
            try:
                cell = ws.find(user_id)
            except gspread.CellNotFound:
                cell = None

            if cell:
                # Actualizar fila existente
                ws.update(f"B{cell.row}:D{cell.row}", [[capital, rate, timestamp]])
            else:
                # Agregar nueva fila
                ws.append_row([user_id, capital, rate, timestamp])
            return True
        except Exception as e:
            print(f"Error saving user config: {e}")
            return False

    def _get_mock_data(self, tab_name):
        if tab_name == "Finanzas": return self._get_mock_finanzas()
        if tab_name == "Propiedades": return self._get_mock_propiedades()
        if tab_name == "Inventario": return self._get_mock_inventario()
        if tab_name == "Vencimientos": return self._get_mock_vencimientos()
        return pd.DataFrame()

    def _get_mock_finanzas(self):
        data = {
            "Fecha": [str(datetime.now().date() - timedelta(days=i*10)) for i in range(5)],
            "Instrumento": ["LECAP S31G6", "ON YPF", "TAMAR", "LECAP S31G6", "CEDEAR SPY"],
            "Capital": [1000000.0, 5000000.0, 250000.0, 1500000.0, 3000000.0],
            "Tasa": [0.45, 0.08, 0.52, 0.44, 0.0], 
            "Vencimiento": [
                str(datetime.now().date() + timedelta(days=2)), 
                str(datetime.now().date() + timedelta(days=180)),
                str(datetime.now().date() + timedelta(days=45)),
                str(datetime.now().date() + timedelta(days=2)),
                str(datetime.now().date() + timedelta(days=365))
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
                str(datetime.now().date() + timedelta(days=2)),
                str(datetime.now().date() + timedelta(days=15)),
                str(datetime.now().date() + timedelta(days=5)),
                str(datetime.now().date() + timedelta(days=30))
            ],
            "Prioridad": ["Alta", "Alta", "Media", "Media"],
            "Estado": ["Pendiente", "Pendiente", "Pendiente", "Pendiente"]
        }
        return pd.DataFrame(data)
