from tkinter import messagebox
from deployment_steps import *
import paramiko
from colorama import init

# Damit es mit CMD und WindowsPS funktioniert
init()

# Farben definieren
YELLOW = '\033[93m'
GREEN = '\033[92m'  
RED = '\033[91m'
RESET = '\033[0m'

def _rollback_and_cleanup(client, conn, cursor, baen, komponente, version, old_version, link, isSoapserver, jboss_conn):
    """
    Führt Rollback wenn Deployment fehlgeschlagenen ist.
    """
    print(f"\n{YELLOW}--- STARTE ROLLBACK ---{RESET}")

    new_filename = ""
    if komponente == "wwsreports":
        new_filename = f"wwsreports-{version}.war"
    elif komponente == "help":
        new_filename = f"wwshelp-{version}.war"
    elif isSoapserver:
        new_filename = f"{link}-{version}.war"
    else:
        new_filename = f"{komponente}-{version}.war"

    # .war-Datei löschen
    print(f" -> [Rollback 1/5] Lösche heruntergeladene Datei: {new_filename}...")
    try:
        if new_filename:
            client.exec_command(f"rm /opt/wildfly/deploy/{new_filename}")
            print("     Datei erfolgreich gelöscht.")
    except Exception as e:
        print(f"    {RED}Warnung: Konnte neue .war-Datei nicht löschen: {e}{RESET}")

    # Wenn für ein Neu-Deployment (ohne alte Version) etwas schiefgeht, ist hier Schluss.
    if not old_version:
        print(f"{GREEN}--- BEREINIGUNG ABGESCHLOSSEN ---{RESET}")
        return

    print(f" -> Versuche, auf die alte Version '{old_version}' zurückzusetzen...")
    try:
        # Die weiteren Schritte werden nur ausgeführt, wenn es eine alte Version zum Wiederherstellen gibt.
        print(f" -> [Rollback 2/5] Undeploy der Komponente '{komponente}'...")
        undeploy_old_version(client, komponente, jboss_conn)

        print(f" -> [Rollback 3/5] Alten Symlink für '{old_version}' wiederherstellen...")
        remove_old_symlink(client, komponente)
        create_new_symlink(client, komponente, old_version, link, isSoapserver)

        print(f" -> [Rollback 4/5] Deploy der alten Version '{old_version}'...")
        deploy_new_version(client, komponente, jboss_conn)

        print(f" -> [Rollback 5/5] Setze Datenbank-Eintrag auf '{old_version}' zurück...")
        update_sysparams(conn, cursor, komponente, old_version, link, isSoapserver, baen)

        print(f"\n{GREEN} -> Rollback auf Version '{old_version}' erfolgreich!{RESET}")

    except Exception as rollback_e:
        print(f"\n{RED}!!! KRITISCHER FEHLER BEIM ROLLBACK: {rollback_e} !!!{RESET}")
        messagebox.showerror("Rollback-Fehler",
                             f"Das automatische Rollback ist fehlgeschlagen: {rollback_e}\n\n"
                             f"BITTE MANUELL PRÜFEN!")

    print(f"{GREEN}--- ROLLBACK abgeschlossen ---{RESET}")

""" für das Aktualisieren einer BESTEHENDEN Komponente. """
def deploy_existing_component(client, decr_root, conn, cursor, baen, komponente, version, cluster_val):
    
    if not komponente or not version or not cluster_val:
        messagebox.showwarning("Warnung", "Cluster, Komponente und Version dürfen nicht leer sein!")
        return

    print("\n" + "="*50)
    print(f"Starte UPDATE-Workflow für: {komponente} v{version} auf {cluster_val}")
    print("="*50)

    try:
        # Verbindung herstellen
        print(f"  -> Stelle SSH-Verbindung zu {cluster_val} her...")
        client.connect(cluster_val, username='root', password=decr_root, look_for_keys=False, allow_agent=False)
        print(f"     Verbindung {GREEN}erfolgreich{RESET}.")

        # Setup
        isSoapserver = komponente in ["wws", "wwsartdecl"]
        link = "soapserver" if isSoapserver else komponente
        jboss_conn = f"/opt/wildfly/bin/jboss-cli.sh --controller={cluster_val}:9999 --user=admin --password=Admin --connect --commands='"
        
        # Ablauf für ein Update
        old_version = find_old_version(client, komponente, link, isSoapserver)
        if not old_version:
            # Sicherheitsabfrage, falls jemand eine neue Komponente im Hauptfenster deployen will
            if not messagebox.askyesno("Komponente nicht gefunden", f"Die Komponente '{komponente}' scheint nicht zu existieren.\nMöchtest du sie als NEUE Komponente deployen?"):
                raise Exception("Prozess vom Benutzer abgebrochen.")

        download_war_file(client, komponente, version, link, isSoapserver)
        if old_version:
            undeploy_old_version(client, komponente, jboss_conn)
            remove_old_symlink(client, komponente)
        create_new_symlink(client, komponente, version, link, isSoapserver)
        deploy_new_version(client, komponente, jboss_conn)
        update_sysparams(conn, cursor, komponente, version, link, isSoapserver, baen)
        if old_version:
            remove_old_war_file(client, komponente, old_version, link, isSoapserver)
        
        messagebox.showinfo("Erfolg", f"Update von '{komponente}' erfolgreich abgeschlossen!")

    except Exception as e:
        messagebox.showerror(f"Prozess {RED}fehlgeschlagen{RESET}", f"Ein Fehler ist aufgetreten:\n\n{e}")
        _rollback_and_cleanup(client, conn, cursor, baen, komponente, version, old_version, link, isSoapserver, jboss_conn)
        return

""" Workflow NUR für das Deployment einer NEUEN Komponente (aus dem Popup). """
def deploy_new_component(client, decr_root, conn, cursor, baen, komponente, version, cluster_val):
    
    if not komponente or not version or not cluster_val:
        messagebox.showwarning("Warnung", "Cluster, Komponente und Version dürfen nicht leer sein!")
        return

    print("\n" + "="*50)
    print(f"Starte NEU-Workflow für: {komponente} v{version} auf {cluster_val}")
    print("="*50)

    try:
        # Verbindung herstellen
        print(f"  -> Stelle SSH-Verbindung zu {cluster_val} her...")
        client.connect(cluster_val, username='root', password=decr_root, look_for_keys=False, allow_agent=False)
        print(f"     Verbindung {GREEN}erfolgreich{RESET}.")

        # Setup
        isSoapserver = komponente in ["wws", "wwsartdecl"]
        link = "soapserver" if isSoapserver else komponente
        jboss_conn = f"/opt/wildfly/bin/jboss-cli.sh --controller={cluster_val}:9999 --user=admin --password=Admin --connect --commands='"

        download_war_file(client, komponente, version, link, isSoapserver)
        create_new_symlink(client, komponente, version, link, isSoapserver)
        deploy_new_version(client, komponente, jboss_conn)
        update_sysparams(conn, cursor, komponente, version, link, isSoapserver, baen)
        
        messagebox.showinfo("Erfolg", f"Deployment von '{komponente}' erfolgreich abgeschlossen!")

    except Exception as e:
        messagebox.showerror(f"Prozess {RED}fehlgeschlagen{RESET}", f"Ein Fehler ist aufgetreten:\n\n{e}")
        _rollback_and_cleanup(client, conn, cursor, baen, komponente, version, None, link, isSoapserver, jboss_conn)
        return

