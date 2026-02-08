import requests

def test_api(url, name):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: OK")
            try: 
                data = response.json()
                # Print a sample to see structure
                sample = str(data)[:200]
                print(f"   Sample: {sample}")
            except:
                print("   (Non-JSON response)")
        else:
            print(f"❌ {name}: Status {response.status_code}")
    except Exception as e:
        print(f"❌ {name}: Failed ({str(e)})")

print("--- Testing Financial APIs ---")

# 1. DolarAPI (Already known, checking for hidden gems)
test_api("https://dolarapi.com/v1/dolares", "DolarAPI")

# 2. ArgentinaDatos (Community API for CER, UVA, etc)
# Intentando endpoints comunes
test_api("https://api.argentinadatos.com/v1/finanzas/indices/uva", "ArgDatos UVA")
test_api("https://api.argentinadatos.com/v1/finanzas/indices/cer", "ArgDatos CER")
test_api("https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo", "ArgDatos Plazo Fijo")

# 3. BCRA (Usually requires auth, testing public endpoints if any)
test_api("https://api.bcra.gob.ar/estadisticas/v2.0/PrincipalesVariables", "BCRA Principales Variables")

# 4. Matba Rofex (Tamar usually requires login, testing public summary if exists)
# Hard to find perfect public one, checking generic generic financial api
