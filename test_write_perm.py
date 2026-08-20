import gspread

try:
    gc = gspread.service_account(filename="service_account.json")
    sh = gc.open_by_key("1hFZVyh6YwzHD13jCZDSs6zqxvJXZ_jNTHRTMh2OaqIM")
    ws = sh.get_worksheet(0)
    val = ws.cell(1, 1).value
    print(f"Lectura exitosa: A1 = '{val}'")
    
    ws.update_cell(1, 1, val)
    print("SUCCESS: PERMISOS DE ESCRITURA CONFIRMADOS! Puede modificar el Sheet con exito.")
except Exception as e:
    print(f"ERROR: {e}")
