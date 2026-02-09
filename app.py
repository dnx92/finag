from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import pandas as pd
from data_manager import DataManager
import utils
import folium
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from authlib.integrations.flask_client import OAuth
from urllib.parse import urlencode
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno locales (.env)
load_dotenv()

from market_data import MarketData

app = Flask(__name__)
# Necesario para sesiones Flask
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_123")

# --- LOGIN SETUP (Auth0) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id=os.environ.get("AUTH0_CLIENT_ID"),
    client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
    api_base_url=f'https://{os.environ.get("AUTH0_DOMAIN")}',
    access_token_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/oauth/token',
    authorize_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

class User(UserMixin):
    def __init__(self, user_id, name="Usuario", email=""):
        self.id = user_id
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    # En un sistema real esto vendría de DB. 
    # Aquí recuperamos info básica de la sesión si existe, o creamos usuario genérico.
    user_info = session.get('user_info')
    if user_info and user_info.get('sub') == user_id:
        return User(user_info['sub'], user_info.get('name'), user_info.get('email'))
    return User(user_id)

dm = DataManager()

# Context Processor para datos globales (Sidebar)
@app.context_processor
def inject_market_data():
    try:
        indicators = MarketData.get_economic_indicators()
    except:
        indicators = {}
    return dict(indicators=indicators)

# API para Configuración Financiera (Ticker)
@app.route('/api/financial-config', methods=['GET', 'POST'])
@login_required
def financial_config():
    if request.method == 'GET':
        config = dm.get_user_config(current_user.id)
        
        # Lógica de "Catch-up" (Poner al día el contador)
        try:
            last_ts = datetime.fromisoformat(config.get('timestamp'))
            now_ts = datetime.now()
            diff_seconds = (now_ts - last_ts).total_seconds()
            
            capital = float(config.get('capital', 0))
            rate = float(config.get('rate', 0))
            balance_historico = float(config.get('balance_historico', 0))
            
            # Ganancia por segundo (Gs)
            gs = (capital * (rate / 100)) / 31536000 # 365 * 24 * 3600
            
            # Nuevo saldo inicial = histórico + (tiempo * ganancia)
            accrued_profit = max(0, diff_seconds * gs)
            current_balance = balance_historico + accrued_profit
            
            config['current_balance'] = current_balance
            config['server_now'] = now_ts.isoformat()
        except Exception as e:
            print(f"Error calculando catch-up balance: {e}")
            config['current_balance'] = config.get('balance_historico', 0)
            
        return jsonify(config)
    
    if request.method == 'POST':
        data = request.json
        print(f"📥 POST /api/financial-config received: {data}")
        
        # El servidor es el dueño del tiempo, pero DataManager ya pone el timestamp.
        # Solo validamos que los datos sean numéricos básicos si fuera necesario, 
        # pero delegamos a DataManager la persistencia del objeto.
        
        success = dm.save_user_config(current_user.id, current_user.email, data)
        if success:
            return jsonify({"status": "success", "server_time": datetime.now().isoformat()})
        else:
            return jsonify({"status": "error"}), 500

@app.route('/debug-sheets')
@login_required
def debug_sheets():
    status = dm.get_status()
    # Forzamos re-intentar conexión si está fallando, para ver el error fresco
    if status['use_mock']:
        dm._authenticate()
        status = dm.get_status()
    
    return jsonify(status)

@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=url_for('callback', _external=True))

@app.route('/callback')
def callback():
    try:
        # Auth0 devuelve el token
        auth0.authorize_access_token()
        resp = auth0.get('userinfo')
        user_info = resp.json()
        
        # Guardar en sesión
        session['user_info'] = user_info
        
        # Loguear en Flask
        user = User(user_info['sub'], user_info.get('name'), user_info.get('email'))
        login_user(user)
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        return f"Error en login: {str(e)}"

@app.route('/login_page')
def login_page():
    # Página intermedia con el botón
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    
    # Redirigir a logout de Auth0
    # IMPORTANTE: La URL 'returnTo' debe estar en "Allowed Logout URLs" en Auth0
    params = {
        'returnTo': url_for('goodbye', _external=True),
        'client_id': os.environ.get("AUTH0_CLIENT_ID")
    }
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))

@app.route('/goodbye')
def goodbye():
    return render_template('logout.html')


@app.route('/')
@login_required
def dashboard():
    # Cargar Datos
    finanzas_df = dm.get_data("Finanzas")
    propiedades_df = dm.get_data("Propiedades")
    inventario_df = dm.get_data("Inventario")
    vencimientos_df = dm.get_data("Vencimientos")
    
    # Cotizaciones Dólar
    dolar_rates = MarketData.get_dolar_rates()

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
                           chart_data=chart_data,
                           dolar_rates=dolar_rates)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
