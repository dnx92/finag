from flask import Flask, render_template, jsonify
import pandas as pd
from data_manager import DataManager
import utils
import folium

app = Flask(__name__)
dm = DataManager()

@app.route('/')
def dashboard():
    # Cargar Datos
    finanzas_df = dm.get_data("Finanzas")
    propiedades_df = dm.get_data("Propiedades")
    inventario_df = dm.get_data("Inventario")
    vencimientos_df = dm.get_data("Vencimientos")

    # Métricas
    pesos_s, ganancia_diaria, capital = utils.calculate_financial_pulse(finanzas_df)
    
    # Alertas
    alerts = utils.check_alerts(vencimientos_df)
    
    # Mapa
    m = folium.Map(location=[-34, -60], zoom_start=6, tiles="CartoDB dark_matter")
    if not propiedades_df.empty:
        # Re-centrar si hay datos
        avg_lat = propiedades_df['Latitud'].mean()
        avg_lon = propiedades_df['Longitud'].mean()
        m.location = [avg_lat, avg_lon]
        
        for _, prop in propiedades_df.iterrows():
             # Buscar inventario asociado
            inv_items = inventario_df[inventario_df['Ubicación'] == prop['Nombre']]
            inv_html = "<b>Inventario:</b><ul>"
            if not inv_items.empty:
                for _, item in inv_items.iterrows():
                    inv_html += f"<li>{item['Item']} ({item['Cantidad']})</li>"
            else:
                inv_html += "<li>Sin items</li>"
            inv_html += "</ul>"
            
            popup_html = f"""
            <div style="width:200px">
                <h6>{prop['Nombre']}</h6>
                <p class="mb-0"><b>Tipo:</b> {prop['Tipo']}</p>
                <p class="mb-0"><b>Sup:</b> {prop['Superficie']} Ha</p>
                <hr class="my-1">
                {inv_html}
            </div>
            """
            
            icon_color = "green" if prop['Tipo'] == "Yerba" else "beige" if prop['Tipo'] == "Madera" else "gray"
            
            folium.Marker(
                [prop['Latitud'], prop['Longitud']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=prop['Nombre'],
                icon=folium.Icon(color=icon_color, icon="leaf", prefix="fa")
            ).add_to(m)

    map_html = m._repr_html_()

    # Tasas para Chart.js
    chart_data = {
        "labels": finanzas_df['Instrumento'].tolist() if not finanzas_df.empty else [],
        "values": (finanzas_df['Tasa']).tolist() if not finanzas_df.empty else [],
        "colors": ['#00FF00' if m == 'ARS' else '#00AAFF' for m in finanzas_df['Moneda']] if not finanzas_df.empty else []
    }
    
    # Benchmarks (Hardcoded para demo)
    chart_data['labels'] += ['Plazo Fijo', 'Inflación', 'Dólar']
    chart_data['values'] += [0.35, 0.40, 0.05]
    chart_data['colors'] += ['#555', '#777', '#28a745']

    return render_template('dashboard.html', 
                           pesos_s=pesos_s, 
                           ganancia=ganancia_diaria, 
                           capital=capital,
                           alerts=alerts,
                           map_html=map_html,
                           chart_data=chart_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
