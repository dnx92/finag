from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import pandas as pd
from data_manager import DataManager
import utils
import folium
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_123") # Cambiar en producción

# Configuración de Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Usuarios (Simulado con variables de entorno)
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin")

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USER:
        return User(user_id)
    return None

dm = DataManager()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USER and password == ADMIN_PASS:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
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
