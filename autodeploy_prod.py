import sys
import authentifizierung
import GUI

# === PRODUKTIV-KONFIGURATION ===
PROD_SERVER = "p_wws"      
PROD_DATABASE = "wwstp"  
PROD_BAEN = "-"
PROD_PORT = 11000
PROD_CLUSTERS = ["server320vmx", "server662vmx", "server3061vmx", "server3161vmx", "server3261vmx"]

print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
print("!!! STARTE IM PROD-UMGEBUNG !!!")
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

# Authentifizierung
client, conn, decr_root = authentifizierung.perform_authentication(
    server=PROD_SERVER, 
    database=PROD_DATABASE,
    port=PROD_PORT
)

# GUI starten
if client and conn and decr_root:
    GUI.start_application(client, conn, decr_root, PROD_BAEN, PROD_CLUSTERS)
else:
    print("\nProgramm wird aufgrund eines Authentifizierungsfehlers beendet.")
    sys.exit(1)