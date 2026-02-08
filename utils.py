import pandas as pd
from datetime import datetime

def check_alerts(vencimientos_df):
    """
    Analiza el dataframe de vencimientos y genera alertas.
    """
    alerts = []
    if vencimientos_df.empty:
        return alerts
    
    today = pd.to_datetime(datetime.now().date())
    
    if not pd.api.types.is_datetime64_any_dtype(vencimientos_df['Fecha Límite']):
        vencimientos_df['Fecha Límite'] = pd.to_datetime(vencimientos_df['Fecha Límite'])

    for _, row in vencimientos_df.iterrows():
        days_diff = (row['Fecha Límite'] - today).days
        
        if 0 <= days_diff <= 3:
            alerts.append({
                "msg": f"⚠️ URGENTE: '{row['Tarea']}' vence en {days_diff} días.",
                "priority": "High",
                "class": "danger" # Bootstrap class
            })
        elif days_diff < 0:
            alerts.append({
                "msg": f"🚨 VENCIDO: '{row['Tarea']}' venció hace {abs(days_diff)} días.",
                "priority": "Critical",
                "class": "dark"
            })
        elif days_diff <= 7:
             alerts.append({
                "msg": f"📅 Próximo: '{row['Tarea']}' vence la próxima semana.",
                "priority": "Medium",
                "class": "warning"
            })
            
    return alerts

def calculate_financial_pulse(finanzas_df):
    """
    Calcula métricas financieras simples.
    """
    if finanzas_df.empty:
        return 0, 0, 0

    finanzas_df['Capital'] = pd.to_numeric(finanzas_df['Capital'], errors='coerce').fillna(0)
    # Limpiar tasa (si viene como string con %) o float
    # Asumimos float directo del mock
    finanzas_df['Tasa'] = pd.to_numeric(finanzas_df['Tasa'], errors='coerce').fillna(0)
    
    total_capital = finanzas_df['Capital'].sum()
    finanzas_df['GananciaDiaria'] = finanzas_df['Capital'] * (finanzas_df['Tasa'] / 365)
    daily_gain = finanzas_df['GananciaDiaria'].sum()
    pesos_per_second = daily_gain / (24 * 60 * 60)
    
    return pesos_per_second, daily_gain, total_capital
