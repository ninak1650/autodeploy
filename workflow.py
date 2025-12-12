from tkinter import messagebox
from deployment_steps import *

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
        print("     Verbindung erfolgreich.")

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
        messagebox.showerror("Prozess fehlgeschlagen", f"Ein Fehler ist aufgetreten:\n\n{e}")
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
        print("     Verbindung erfolgreich.")

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
        messagebox.showerror("Prozess fehlgeschlagen", f"Ein Fehler ist aufgetreten:\n\n{e}")
        return

