import pandas as pd
from data_manager import DataManager
import os

def create_templates():
    dm = DataManager()
    
    # Forzamos uso de mock para obtener la estructura base
    dm.use_mock = True
    
    sheets = {
        "Finanzas": dm._get_mock_finanzas(),
        "Propiedades": dm._get_mock_propiedades(),
        "Inventario": dm._get_mock_inventario(),
        "Vencimientos": dm._get_mock_vencimientos()
    }
    
    output_dir = "plantillas_csv"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generando plantillas en carpet '{output_dir}'...")
    
    for name, df in sheets.items():
        file_path = f"{output_dir}/{name}.csv"
        df.to_csv(file_path, index=False)
        print(f"✅ {name}.csv creado.")
        
    print("\n¡Listo! Sube estos archivos a tu Google Sheet (en pestañas separadas) para empezar.")

if __name__ == "__main__":
    create_templates()
