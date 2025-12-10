from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode, urlsafe_b64decode
import os
import paramiko
import getpass
import re
import tkinter as tk; from tkinter import ttk, messagebox
import pyodbc

enter_pass = True
global conn
global cursor
client = paramiko.SSHClient()
server = "p_wwsdev2" #server = "p_wws"  
username = "chensaso"  
baen = "-412133"
database = "wwst3"  #database = "wwstp"  
# DATABASE CONNECTION
while(enter_pass):
    sybase_pass = getpass.getpass(prompt="Gib saso Passwort von p_wwsdev2 ein:")
    connection_string = f'DRIVER={{Adaptive Server Enterprise}};SERVER={server};PORT=20000;DATABASE={database};UID={username};PWD={sybase_pass}'   #11000
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        if(cursor):
            enter_pass = False
    except pyodbc.Error as e:
        if "Login failed" in str(e):
            print("Login failed, please try again.")
            enter_pass = True
        else:
            print("An error occured, aborting: {e}")
            enter_pass = False
            os._exit(1)

# DECRYPTION LOGIC
encr_root = "gAAAAABoEfMBo7LMVNeSN5YWJ3L2P3B7EARh3_EUJd7f0cIWKxGBki0AJmMEzPWMcQxTBRjiXd2rIXEQmnGDQtdg1MKOOTGZobdyZnsUG8hoVjEy0GpWQYQ="
salt = b"UIy4SDkwW9a6gQkUrjXDBg=="
passphrase = os.environ["DB_PASSPHRASE"].encode()
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=urlsafe_b64decode(salt),
    iterations=100_000,
    backend=default_backend() 
)
key = urlsafe_b64encode(kdf.derive(passphrase))
fernet = Fernet(key)
decr_root = fernet.decrypt(encr_root.encode())

def update_komponenten(event):
    master = cluster.get()
    master_conn(master)
    java_komponenten = java_komp(master)
    komponenten.set('')
    input_box.delete(0, tk.END)
    komponenten['values'] = java_komponenten


def master_conn(master):
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(master, username='root', password=decr_root.decode(), look_for_keys=False, allow_agent=False)          
    except Exception as e:
        print(f"An error occurred: {e}")
    


def java_komp(master):
    nill, stdout, stderr = client.exec_command("/opt/wildfly/bin/jboss-cli.sh --controller=" + master + ":9999 --user=admin --password=Admin --connect --commands='deploy -l'" )
    output = stdout.read().decode('utf-8', errors='ignore').splitlines()
    java_komp = []
    for line in output[1:-1]:
        if "jmx.war" not in line:
            java_komp.append(line.partition(".war")[0])
    return java_komp

        

def deployKomp(komponente, version, cluster_val, is_new_component=False):
    """
    Führt den gesamten Deploy-Prozess für eine Komponente durch.
    Kann sowohl Updates (is_new_component=False) als auch neue Deploys (is_new_component=True) durchführen.
    """
    # === Vorbereitung und Validierung ===
    if not komponente or not version or not cluster_val:
        messagebox.showwarning("Warnung", "Cluster, Komponente und Version dürfen nicht leer sein!")
        return

    print(f"Starte Deploy-Prozess für: {komponente} v{version} auf {cluster_val}")
    if is_new_component:
        print("Modus: Neue Komponente")
    else:
        print("Modus: Bestehende Komponente aktualisieren")

    # Variablen-Setup basierend auf deiner Logik
    isSoapserver = komponente in ["wws", "wwsartdecl"]
    link = "soapserver" if isSoapserver else komponente
    
    # Pfade und Befehle
    nav = "cd /opt/wildfly/deploy && "
    jboss_conn = f"/opt/wildfly/bin/jboss-cli.sh --controller={cluster_val}:9999 --user=admin --password=Admin --connect --commands='"

    try:
        # === SCHRITT 3: Alte Version finden (nur bei Update) ===
        old_version = None
        if not is_new_component:
            print("Schritt 3: Suche nach alter Version...")
            get_komp_cmd = nav + "ls " + (link if isSoapserver else komponente) + "-*"
            
            nill, stdout, stderr = client.exec_command(get_komp_cmd)
            output = stdout.read().decode('utf-8', errors='ignore').splitlines()

            if output:
                # Extrahiere die Versionsnummer aus dem Dateinamen
                if komponente == "help":
                    old_version = output[0].replace("wwshelp-", "")[:-4]
                else:
                    old_version = output[0].replace((link if isSoapserver else komponente) + "-", "")[:-4]
                print(f"  -> Alte Version gefunden: {old_version}")
            else:
                print("  -> Keine alte Version gefunden. Der Prozess wird als 'neue Komponente' behandelt.")
                is_new_component = True # Wenn nichts da ist, ist es effektiv ein neues Deploy

        # === SCHRITT 4: WAR-Datei herunterladen (wget) ===
        print("Schritt 4: Lade neue .war-Datei herunter...")
        # URL-Logik aus deinem Code übernommen
        if komponente == "wwsreports":
            wget = f"wget http://wwsrepo.mueller.de/repository/handelsmanagement/wwsreports/{version.split('-')[0]}/{version.split('-')[1]}/wwsreports-{version}.war"
        elif komponente == "help":
            wget = f"wget http://wwsrepo.mueller.de/repository/handelsmanagement/wwshelp/{version.split('-')[0]}/{version.split('-')[1]}/wwshelp-{version}.war"
        elif isSoapserver:
            wget = f"wget http://wwsrepo.mueller.de/repository/maven-releases/de/mueller/erp/apps/{link}/{version}/{link}-{version}.war"
        else:
            wget = f"wget http://wwsrepo.mueller.de/repository/maven-releases/de/mueller/erp/apps/{komponente}/{version}/{komponente}-{version}.war"

        # 'wwsartdecl' hat anscheinend keinen Download-Schritt in deinem Code, das wird hier respektiert
        if komponente != "wwsartdecl":
            nill, stdout, stderr = client.exec_command(nav + wget)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8')
                if "ERROR 404: Not Found" in error_output:
                    messagebox.showerror("Fehler bei wget", f"Die Version '{version}' wurde im Repository nicht gefunden (404).")
                    return # Prozess abbrechen
                else:
                    raise Exception(f"wget fehlgeschlagen: {error_output}")
        print("  -> Download erfolgreich.")

        # === SCHRITT 6 & 7: Undeploy und alten Link löschen (nur bei Update) ===
        if not is_new_component:
            print("Schritt 6: Undeploy der alten Version...")
            undeploy_cmd = jboss_conn + "undeploy " + komponente + ".war" + " --all-relevant-server-groups'"
            # Deine Retry-Logik für den Timeout
            retry_cnt = 0
            while retry_cnt < 3:
                nill, stdout, stderr = client.exec_command(undeploy_cmd)
                if stdout.channel.recv_exit_status() == 0:
                    print("  -> Undeploy erfolgreich.")
                    retry_cnt = 10 # Erfolg, Schleife verlassen
                    break
                else:
                    output = stderr.read().decode('utf-8')
                    if "timed out" in output:
                        retry_cnt += 1
                        print(f"  -> Undeploy Timeout, versuche erneut ({retry_cnt}/3)...")
                    else:
                        raise Exception(f"Undeploy fehlgeschlagen: {output}")
            if retry_cnt < 10:
                raise Exception("Undeploy ist nach 3 Versuchen fehlgeschlagen.")

            print("Schritt 7: Lösche alten Symlink...")
            rm_link_cmd = "rm /opt/wildfly/deploy/" + komponente + ".war"
            nill, stdout, stderr = client.exec_command(rm_link_cmd)
            if stdout.channel.recv_exit_status() != 0:
                error_output = stderr.read().decode('utf-8')
                if "No such file or directory" not in error_output:
                    raise Exception(f"Löschen des Links fehlgeschlagen: {error_output}")
                else:
                    print("  -> Kein alter Link vorhanden, wird übersprungen.")
            else:
                print("  -> Alter Link gelöscht.")

        # === SCHRITT 8: Neuen Link setzen ===
        print("Schritt 8: Setze neuen Symlink...")
        if komponente == "help":
            new_link_cmd = f"ln -s /opt/wildfly/deploy/wwshelp-{version}.war /opt/wildfly/deploy/{komponente}.war"
        else:
            new_link_cmd = f"ln -s /opt/wildfly/deploy/{link}-{version}.war /opt/wildfly/deploy/{komponente}.war"
        
        nill, stdout, stderr = client.exec_command(new_link_cmd)
        if stdout.channel.recv_exit_status() != 0:
            raise Exception(f"Setzen des neuen Links fehlgeschlagen: {stderr.read().decode('utf-8')}")
        print("  -> Neuer Link erfolgreich gesetzt.")

        # === SCHRITT 10: Neue Version deployen ===
        print("Schritt 10: Deploy der neuen Version...")
        deploy_cmd = jboss_conn + f"deploy /opt/wildfly/deploy/{komponente}.war --name={komponente}.war --runtime-name={komponente}.war --all-server-groups'"
        nill, stdout, stderr = client.exec_command(deploy_cmd)
        if stdout.channel.recv_exit_status() != 0:
            raise Exception(f"Deploy der neuen Version fehlgeschlagen: {stderr.read().decode('utf-8')}")
        print("  -> Deploy erfolgreich.")

        # === SCHRITT 11: SYSPARAMs aktualisieren ===
        print("Schritt 11: Aktualisiere SYSPARAMs in der Datenbank...")
        if komponente not in ["wwsreports", "wwsartdecl", "help", "jmxservice"]:
            sysitem_name = (link.upper() if isSoapserver else komponente.upper())
            set_min_sql = f"UPDATE SYSPARAM SET WERT = '{version}', DAEN = getdate(), BAEN = {baen} WHERE SYSITEM = 'VERSION.{sysitem_name}.MIN'"
            set_opt_sql = f"UPDATE SYSPARAM SET WERT = '{version}', DAEN = getdate(), BAEN = {baen} WHERE SYSITEM = 'VERSION.{sysitem_name}.OPT'"
            
            cursor.execute(set_min_sql)
            cursor.execute(set_opt_sql)
            conn.commit()
            print(f"  -> DB-Update für VERSION.{sysitem_name} auf '{version}' ausgeführt.")
        else:
            print("  -> Komponente benötigt kein DB-Update, wird übersprungen.")

        # === SCHRITT 12: Alte Version löschen (nur bei Update) ===
        if not is_new_component and old_version:
            print("Schritt 12: Lösche alte .war-Datei...")
            if komponente == "help":
                rm_old_cmd = f"rm -r /opt/wildfly/deploy/wwshelp-{old_version}.war"
            else:
                rm_old_cmd = f"rm -r /opt/wildfly/deploy/{(link if isSoapserver else komponente)}-{old_version}.war"

            nill, stdout, stderr = client.exec_command(rm_old_cmd)
            if stdout.channel.recv_exit_status() != 0:
                # Dies als Warnung behandeln, da der Haupt-Deploy erfolgreich war
                print(f"  -> WARNUNG: Löschen der alten Version '{old_version}' fehlgeschlagen: {stderr.read().decode('utf-8')}")
            else:
                print("  -> Alte .war-Datei erfolgreich gelöscht.")
        
        # --- Abschluss ---
        messagebox.showinfo("Erfolg", f"Deploy von '{komponente}' erfolgreich abgeschlossen!")
        # Optional: Felder im Hauptfenster leeren
        if not is_new_component:
            komponenten.set('')
            input_box.delete(0, tk.END)

    except Exception as e:
        # Generelle Fehlerbehandlung für den gesamten Prozess
        print(f"FEHLER im Deploy-Prozess: {e}")
        messagebox.showerror("Prozess fehlgeschlagen", f"Ein Fehler ist aufgetreten:\n\n{e}")




# ===== NEU: Das modale Popup-Fenster =====
def open_new_component_popup(parent, style_font):
    popup = tk.Toplevel(parent)
    popup.title("Neue Komponente deployen")
    popup.resizable(False, False)
    popup.transient(parent) # An Hauptfenster binden
    
    # Zentrieren
    parent.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - 420) // 2
    y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
    popup.geometry(f"420x200+{x}+{y}")
    
    # Eingabefelder
    ttk.Label(popup, text="Cluster:", font=style_font).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    cluster_entry = ttk.Combobox(popup, values=["server690vmx", "server320vmx"], width=25, font=style_font) # Füge hier alle Cluster hinzu
    cluster_entry.grid(row=0, column=1, padx=12, pady=10, sticky="we")

    ttk.Label(popup, text="Komponente:", font=style_font).grid(row=1, column=0, padx=10, pady=10, sticky="w")
    komponent_entry = ttk.Entry(popup, font=style_font, width=25)
    komponent_entry.grid(row=1, column=1, padx=12, pady=5, sticky="we")

    ttk.Label(popup, text="Version:", font=style_font).grid(row=2, column=0, padx=10, pady=10, sticky="w")
    version_entry = ttk.Entry(popup, font=style_font, width=25)
    version_entry.grid(row=2, column=1, padx=12, pady=5, sticky="we")

    def on_deploy_new():
        # Rufe die zentrale Funktion auf, aber setze 'is_new_component' auf True
        deployKomp(
            komponent_entry.get(),
            version_entry.get(),
            cluster_entry.get(),
            is_new_component=True
        )
        popup.destroy() # Schließe das Popup nach dem Versuch

    deploy_btn = ttk.Button(popup, text="Deploy", command=on_deploy_new)
    deploy_btn.grid(row=3, column=1, pady=15, sticky="e", padx=12)

    # === DAS BLOCKIEREN DES HAUPTFENSTERS ===
    popup.grab_set()       # Blockiert andere Fenster
    parent.wait_window(popup) # Wartet, bis dieses Fenster geschlossen wird

# --- Hauptfenster (root) ---
root = tk.Tk()
root.title("Wildfly ausliefern")
root.geometry("420x200")
root.resizable(False, False)
global_font = ("Arial", 13)

style = ttk.Style()
style.configure("TCombobox", font=global_font)
style.configure("TLabel", font=global_font)
root.columnconfigure(1, weight=1)

# Widgets im Hauptfenster...
lbl_cluster = ttk.Label(root, text="Cluster:")
lbl_cluster.grid(row=0, column=0, padx=(12, 6), pady=(10, 5), sticky="e")
cluster = ttk.Combobox(root, values=["server690vmx", "server320vmx"], width=30)
cluster.grid(row=0, column=1, padx=(6, 12), pady=(10, 5), sticky="we")

lbl_komp = ttk.Label(root, text="Komponente:")
lbl_komp.grid(row=1, column=0, padx=(12, 6), pady=5, sticky="e")
komponenten = ttk.Combobox(root, values=[], width=30)
komponenten.grid(row=1, column=1, padx=(6, 12), pady=5, sticky="we")

lbl_version = ttk.Label(root, text="Version:")
lbl_version.grid(row=2, column=0, padx=(12, 6), pady=(5, 12), sticky="e")
input_box = tk.Entry(root, font=global_font, width=30)
input_box.grid(row=2, column=1, padx=(6, 12), pady=(5, 12), sticky="we")

# --- Buttons im Hauptfenster ---
btn_row = ttk.Frame(root)
btn_row.grid(row=3, column=0, columnspan=2, pady=8)

# Ruft deployKomp auf, Standardwert is_new_component=False wird verwendet
update_btn = ttk.Button(btn_row, text="Aktualisieren", command=lambda: deployKomp(komponenten.get(), input_box.get(), cluster.get()))
update_btn.pack(side=tk.LEFT, padx=8)

# Ruft die Popup-Funktion auf
new_btn = ttk.Button(btn_row, text="Neue Komponente", command=lambda: open_new_component_popup(root, global_font))
new_btn.pack(side=tk.LEFT, padx=8)

cluster.bind("<<ComboboxSelected>>", update_komponenten)
# Start the GUI
root.mainloop()

# --- Verbindungen schließen ---
client.close()
conn.close()