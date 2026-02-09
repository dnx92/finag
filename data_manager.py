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
        self.last_error = None
        
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
                self.last_error = f"Local Auth Error: {str(e)}"
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
                self.last_error = f"Env Var Auth Error: {str(e)}"
                print(f"❌ Error Auth Env Var: {e}")
        else:
             self.last_error = "No GOOGLE_CREDENTIALS_JSON found in Environment."

        print("ℹ️ No se encontraron credenciales válidas. Usando MOCK DATA.")
        self.use_mock = True

    def _connect_sheet(self):
        try:
            self.sheet = self.client.open(self.sheet_name)
            self.use_mock = False
            self.last_error = "Connected OK"
            print(f"✅ Conectado exitosamente a Google Sheet: {self.sheet_name}")
        except Exception as e:
            self.last_error = f"Sheet Open Error: {str(e)}"
            print(f"⚠️ Error al abrir la hoja '{self.sheet_name}': {e}")
            self.use_mock = True

    def get_status(self):
        usuarios_status = "Unknown"
        if not self.use_mock and self.sheet:
            try:
                self.sheet.worksheet("Usuarios")
                usuarios_status = "Found ✅"
            except Exception as e:
                usuarios_status = f"Missing/Error ❌: {str(e)}"

        return {
            "use_mock": self.use_mock,
            "last_error": self.last_error,
            "sheet_name": self.sheet_name,
            "env_var_present": bool(os.environ.get("GOOGLE_CREDENTIALS_JSON")),
            "usuarios_tab": usuarios_status
        }

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
                # Helper para convertir string a float (manejo de comas)
                def to_float(val):
                    if isinstance(val, (int, float)): return float(val)
                    if isinstance(val, str):
                        val = val.replace(',', '.').strip()
                        if not val: return 0.0
                        return float(val)
                    return 0.0

                # Orden: ID, Email, Capital, Tasa, Timestamp, Balance_Historico
                # Ajustamos índices (+1 por el email insertado)
                capital = to_float(row_values[2]) if len(row_values) > 2 else 0
                rate = to_float(row_values[3]) if len(row_values) > 3 else 0
                timestamp = row_values[4] if len(row_values) > 4 else datetime.now().isoformat()
                balance_historico = to_float(row_values[5]) if len(row_values) > 5 else 0.0
                
                return {
                    "capital": capital,
                    "rate": rate,
                    "timestamp": timestamp,
                    "balance_historico": balance_historico
                }
            return default_config
        except Exception as e:
            print(f"Error config: {e}")
            return default_config

    def save_user_config(self, user_id, user_email, config_data):
        if self.use_mock:
            print(f"Mock Save: {user_id} ({user_email}) -> {config_data}")
            return True

        try:
            ws = self.sheet.worksheet("Usuarios")
            timestamp = datetime.now().isoformat()
            
            # Buscar específicamente en la Columna 1 (ID)
            try:
                cell = ws.find(user_id, in_column=1)
            except (gspread.CellNotFound, gspread.exceptions.CellNotFound):
                cell = None

            # Datos a extraer
            capital = float(config_data.get('capital', 0))
            rate = float(config_data.get('rate', 0))
            balance = float(config_data.get('balance_historico', 0))

            row_data = [user_id, user_email, float(capital), float(rate), timestamp, balance]

            if cell:
                # El rango es A{row}:F{row}
                range_label = f"A{cell.row}:F{cell.row}"
                ws.update(range_label, [row_data])
            else:
                # Append: ID, Email, Capital, Tasa, Timestamp, Balance_Historico
                ws.append_row(row_data)
                
            print(f"✅ Configuración guardada para: {user_email}")
            return True
        except Exception as e:
            print(f"❌ Error al guardar en Sheets: {e}")
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
