import sys
import authentifizierung
import GUI

# === TEST-KONFIGURATION ===
TEST_SERVER = "p_wwsdev2"
TEST_DATABASE = "wwst3"
TEST_BAEN = "-"
TEST_PORT = 20000
TEST_CLUSTERS = ["server690vmx", "server662vmx"]

# Farben definieren
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

print("===============================")
print(f"=== STARTE IM {YELLOW}TEST-UMGEBUNG{RESET} ===")
print("===============================")

# Authentifizierung
client, conn, decr_root = authentifizierung.perform_authentication(
    server=TEST_SERVER, 
    database=TEST_DATABASE,
    port=TEST_PORT
)

# GUI starten
if client and conn and decr_root:
    GUI.start_application(client, conn, decr_root, TEST_BAEN, TEST_CLUSTERS)
else:
    print(f"\n{RED}Programm wird aufgrund eines Authentifizierungsfehlers beendet.")
    sys.exit(1)