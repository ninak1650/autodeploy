import sys
import authentifizierung
import GUI

# === TEST-KONFIGURATION ===
TEST_SERVER = "p_wwsdev2"
TEST_DATABASE = "wwst3"
TEST_BAEN = "-"
TEST_PORT = 20000
TEST_CLUSTERS = ["server690vmx"]

print("===============================")
print("=== STARTE IM TEST-UMGEBUNG ===")
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
    print("\nProgramm wird aufgrund eines Authentifizierungsfehlers beendet.")
    sys.exit(1)