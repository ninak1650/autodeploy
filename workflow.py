from tkinter import messagebox
from deployment_steps import *

# === Das Deployment ===
def run_deployment_workflow(client, conn, cursor, baen, komponente, version, cluster_val, is_new_component=False):
    """Führt den kompletten Workflow durch Aufruf der Einzelschritte aus."""
    if not komponente or not version or not cluster_val:
        messagebox.showwarning("Warnung", "Cluster, Komponente und Version dürfen nicht leer sein!")
        return

    print(f"\nStarte Deploy-Workflow für: {komponente} v{version} auf {cluster_val}")
    print(f"Modus: {'Neue Komponente' if is_new_component else 'Bestehende Komponente aktualisieren'}")

    # Setup
    isSoapserver = komponente in ["wws", "wwsartdecl"]
    link = "soapserver" if isSoapserver else komponente
    jboss_conn = f"/opt/wildfly/bin/jboss-cli.sh --controller={cluster_val}:9999 --user=admin --password=Admin --connect --commands='"

    try:
        # --- Workflow-Schritte ---
        old_version = find_old_version(client, komponente, link, isSoapserver)
        if not old_version:
             is_new_component = True # Wenn nichts da ist, ist es ein neues Deploy

        download_war_file(client, komponente, version, link, isSoapserver)

        if not is_new_component:
            undeploy_old_version(client, komponente, jboss_conn)
            remove_old_symlink(client, komponente)

        create_new_symlink(client, komponente, version, link, isSoapserver)
        deploy_new_version(client, komponente, jboss_conn)
        update_sysparams(conn, cursor, komponente, version, link, isSoapserver, baen)

        if not is_new_component and old_version:
            remove_old_war_file(client, komponente, old_version, link, isSoapserver)
        
        # Erfolg!
        messagebox.showinfo("Erfolg", f"Deploy von '{komponente}' erfolgreich abgeschlossen!")

    except Exception as e:
        # Wenn irgendein Schritt fehlschlägt, den Fehler wurde hier abgefangen.
        print(f"FEHLER im Workflow: {e}")
        messagebox.showerror("Prozess fehlgeschlagen", f"Ein Fehler ist aufgetreten:\n\n{e}")

