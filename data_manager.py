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
        # 1. Intentar archivo local (Dev)
        if os.path.exists(self.creds_file):
            try:
                self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, self.scope)
                self.client = gspread.authorize(self.creds)
                self._connect_sheet()
                return
            except Exception as e:
                print(f"❌ Error Auth Archivo Local: {e}")

        # 2. Intentar Variable de Entorno (Render/Prod)
        evar_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if evar_creds:
            try:
                creds_dict = json.loads(evar_creds)
                self.creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, self.scope)
                self.client = gspread.authorize(self.creds)
                self._connect_sheet()
                return
            except Exception as e:
                print(f"❌ Error Auth Env Var: {e}")

        print("ℹ️ No se encontraron credenciales válidas. Usando MOCK DATA.")
        self.use_mock = True

    def _connect_sheet(self):
        try:
            self.sheet = self.client.open(self.sheet_name)
            self.use_mock = False
            print(f"✅ Conectado exitosamente a Google Sheet: {self.sheet_name}")
        except Exception as e:
            print(f"⚠️ Error al abrir la hoja '{self.sheet_name}': {e}")
            self.use_mock = True

    @cachetools.func.ttl_cache(maxsize=10, ttl=60)
    def get_data(self, sheet_tab):
        if self.use_mock:
            return self._get_mock_data(sheet_tab)
        
        try:
            worksheet = self.sheet.worksheet(sheet_tab)
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error leyendo {sheet_tab}: {e}")
            return self._get_mock_data(sheet_tab)

    def get_user_config(self, user_id):
        default_config = {"capital": 0, "rate": 0, "timestamp": datetime.now().isoformat()}
        if self.use_mock: return default_config

        try:
            ws = self.sheet.worksheet("Usuarios")
            cell = ws.find(user_id)
            if cell:
                row_values = ws.row_values(cell.row)
                # Orden: ID, Email, Capital, Tasa, Timestamp
                # Ajustamos índices (+1 por el email insertado)
                return {
                    "capital": float(row_values[2]) if len(row_values) > 2 else 0,
                    "rate": float(row_values[3]) if len(row_values) > 3 else 0,
                    "timestamp": row_values[4] if len(row_values) > 4 else datetime.now().isoformat()
                }
            return default_config
        except Exception as e:
            print(f"Error config: {e}")
            return default_config

    def save_user_config(self, user_id, user_email, capital, rate):
        if self.use_mock:
            print(f"Mock Save: {user_id} ({user_email}) -> ${capital}")
            return True

        try:
            ws = self.sheet.worksheet("Usuarios")
            timestamp = datetime.now().isoformat()
            
            try:
                cell = ws.find(user_id)
            except gspread.CellNotFound:
                cell = None

            if cell:
                # Actualizar: ID(1), Email(2), Capital(3), Tasa(4), Time(5)
                # gspread usa 1-based index. Cell row es la fila.
                # Queremos actualizar col 2,3,4,5
                ws.update_cell(cell.row, 2, user_email) # Actualizar email por si cambió
                ws.update_cell(cell.row, 3, capital)
                ws.update_cell(cell.row, 4, rate)
                ws.update_cell(cell.row, 5, timestamp)
            else:
                # Append: ID, Email, Capital, Tasa, Timestamp
                ws.append_row([user_id, user_email, capital, rate, timestamp])
            return True
        except Exception as e:
            print(f"Error saving: {e}")
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
