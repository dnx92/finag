from data_manager import DataManager
import os
import json

print("--- DIAGNOSTICO DE CONEXION DE GOOGLE SHEETS ---")

# Verificar si existe local
print(f"1. Archivo credentials.json existe? {os.path.exists('credentials.json')}")

# Verificar variable de entorno
env_var = os.environ.get("GOOGLE_CREDENTIALS_JSON")
print(f"2. Variable GOOGLE_CREDENTIALS_JSON detectada? {'SÍ' if env_var else 'NO'}")

print("\n3. Intentando conectar DataManager...")
try:
    dm = DataManager()
    print(f"   Estado MOCK: {dm.use_mock}")
    if dm.use_mock:
        print("   ❌ FALLO: DataManager está usando Mock.")
    else:
        print("   ✅ EXITO: Conectado a Google Sheets.")
        
        print("\n4. Probando lectura/escritura en pestaña 'Usuarios'...")
        try:
            # Test Save
            test_id = "test_user_conn"
            test_email = "test@connection.com"
            print("   -> Intentando guardar datos de prueba...")
            res = dm.save_user_config(test_id, test_email, 12345, 10.5)
            if res:
                print("   ✅ Escritura OK")
            else:
                print("   ❌ Fallo escritura")
            
            # Test Read
            print("   -> Intentando leer datos...")
            cfg = dm.get_user_config(test_id)
            print(f"   ✅ Lectura: {cfg}")
            
        except Exception as e:
            print(f"   ❌ Error en operaciones: {e}")

except Exception as e:
    print(f"❌ Error fatal al iniciar DataManager: {e}")
