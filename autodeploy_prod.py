import sys
import authentifizierung
import GUI

# === PRODUKTIV-KONFIGURATION ===
PROD_SERVER = "p_wws"      
PROD_DATABASE = "wwstp"  
PROD_BAEN = "-"      #PSNR, anpassen!

print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
print("!!! STARTE IM PROD-UMGEBUNG !!!")
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

# 1. Authentifizierung
client, conn, decr_root = authentifizierung.perform_authentication(
    server=PROD_SERVER, 
    database=PROD_DATABASE
)

# 2. GUI starten
if client and conn and decr_root:
    GUI.start_application(client, conn, decr_root, PROD_BAEN)
else:
    print("\nProgramm wird aufgrund eines Authentifizierungsfehlers beendet.")
    sys.exit(1)