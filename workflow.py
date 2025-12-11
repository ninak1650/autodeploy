from tkinter import messagebox 

def find_old_version(client, komponente, link, isSoapserver):
    """Sucht nach einer alten Version der Komponente und gibt die Version zurück."""
    print("  -> Suche nach alter Version...")
    nav = "cd /opt/wildfly/deploy && "
    get_komp_cmd = nav + "ls " + (link if isSoapserver else komponente) + "-*"
    
    _, stdout, _ = client.exec_command(get_komp_cmd)
    output = stdout.read().decode('utf-8').splitlines()

    if output:
        if komponente == "help":
            old_version = output[0].replace("wwshelp-", "")[:-4]
        else:
            old_version = output[0].replace((link if isSoapserver else komponente) + "-", "")[:-4]
        print(f"     Alte Version gefunden: {old_version}")
        return old_version
    
    print("     Keine alte Version gefunden.")
    return None

def download_war_file(client, komponente, version, link, isSoapserver):
    """Lädt die angegebene .war-Datei aus dem Repository herunter."""
    print("  -> Lade neue .war-Datei herunter...")
    nav = "cd /opt/wildfly/deploy && "

    if komponente == "wwsreports":
        wget_cmd = f"wget http://wwsrepo.mueller.de/repository/handelsmanagement/wwsreports/{version.split('-')[0]}/{version.split('-')[1]}/wwsreports-{version}.war"
    elif komponente == "help":
        wget_cmd = f"wget http://wwsrepo.mueller.de/repository/handelsmanagement/wwshelp/{version.split('-')[0]}/{version.split('-')[1]}/wwshelp-{version}.war"
    elif isSoapserver:
        wget_cmd = f"wget http://wwsrepo.mueller.de/repository/maven-releases/de/mueller/erp/apps/{link}/{version}/{link}-{version}.war"
    else:
        wget_cmd = f"wget http://wwsrepo.mueller.de/repository/maven-releases/de/mueller/erp/apps/{komponente}/{version}/{komponente}-{version}.war"

    if komponente != "wwsartdecl":
        _, stdout, stderr = client.exec_command(nav + wget_cmd)
        if stdout.channel.recv_exit_status() != 0:
            raise Exception(f"wget fehlgeschlagen: {stderr.read().decode('utf-8')}")
    print("     Download erfolgreich.")

def undeploy_old_version(client, komponente, jboss_conn):
    """Führt 'undeploy' auf dem JBoss-Server aus."""
    print("  -> Undeploy der alten Version...")
    undeploy_cmd = jboss_conn + "undeploy " + komponente + ".war --all-relevant-server-groups'"
    
    for i in range(3):
        _, stdout, stderr = client.exec_command(undeploy_cmd)
        if stdout.channel.recv_exit_status() == 0:
            print("     Undeploy erfolgreich.")
            return
        else:
            output = stderr.read().decode('utf-8')
            if "timed out" in output:
                print(f"     Undeploy Timeout, versuche erneut ({i+1}/3)...")
            else:
                raise Exception(f"Undeploy fehlgeschlagen: {output}")
    raise Exception("Undeploy ist nach 3 Versuchen fehlgeschlagen.")

def remove_old_symlink(client, komponente):
    """Löscht den alten Symlink im Deploy-Verzeichnis."""
    print("  -> Lösche alten Symlink...")
    rm_link_cmd = "rm /opt/wildfly/deploy/" + komponente + ".war"
    _, _, stderr = client.exec_command(rm_link_cmd)
    error = stderr.read().decode('utf-8')
    if error and "No such file or directory" not in error:
         raise Exception(f"Löschen des Links fehlgeschlagen: {error}")
    print("     Alter Link gelöscht oder war nicht vorhanden.")

def create_new_symlink(client, komponente, version, link, isSoapserver):
    """Erstellt den neuen Symlink zur neuen .war-Datei."""
    print("  -> Setze neuen Symlink...")
    if komponente == "help":
        new_link_cmd = f"ln -s /opt/wildfly/deploy/wwshelp-{version}.war /opt/wildfly/deploy/{komponente}.war"
    else:
        new_link_cmd = f"ln -s /opt/wildfly/deploy/{link}-{version}.war /opt/wildfly/deploy/{komponente}.war"
    
    _, _, stderr = client.exec_command(new_link_cmd)
    if stderr.read():
        raise Exception(f"Setzen des neuen Links fehlgeschlagen: {stderr.read().decode('utf-8')}")
    print("     Neuer Link erfolgreich gesetzt.")

def deploy_new_version(client, komponente, jboss_conn):
    """Führt 'deploy' der neuen Version auf dem JBoss-Server aus."""
    print("  -> Deploy der neuen Version...")
    deploy_cmd = jboss_conn + f"deploy /opt/wildfly/deploy/{komponente}.war --name={komponente}.war --runtime-name={komponente}.war --all-server-groups'"
    _, _, stderr = client.exec_command(deploy_cmd)
    if stderr.read():
        raise Exception(f"Deploy der neuen Version fehlgeschlagen: {stderr.read().decode('utf-8')}")
    print("     Deploy erfolgreich.")

def update_sysparams(conn, cursor, komponente, version, link, isSoapserver, baen):
    """Aktualisiert die SYSPARAM-Tabelle in der Datenbank."""
    if komponente not in ["wwsreports", "wwsartdecl", "help", "jmxservice"]:
        print("  -> Aktualisiere SYSPARAMs in der Datenbank...")
        sysitem_name = (link.upper() if isSoapserver else komponente.upper())
        set_min_sql = f"UPDATE SYSPARAM SET WERT = '{version}', DAEN = getdate(), BAEN = {baen} WHERE SYSITEM = 'VERSION.{sysitem_name}.MIN'"
        set_opt_sql = f"UPDATE SYSPARAM SET WERT = '{version}', DAEN = getdate(), BAEN = {baen} WHERE SYSITEM = 'VERSION.{sysitem_name}.OPT'"
        
        cursor.execute(set_min_sql)
        cursor.execute(set_opt_sql)
        conn.commit()
        print(f"     DB-Update für VERSION.{sysitem_name} auf '{version}' ausgeführt.")
    else:
        print("  -> Komponente benötigt kein DB-Update, wird übersprungen.")

def remove_old_war_file(client, komponente, old_version, link, isSoapserver):
    """Löscht die alte .war-Datei vom Server."""
    print("  -> Lösche alte .war-Datei...")
    if komponente == "help":
        rm_old_cmd = f"rm -r /opt/wildfly/deploy/wwshelp-{old_version}.war"
    else:
        rm_old_cmd = f"rm -r /opt/wildfly/deploy/{(link if isSoapserver else komponente)}-{old_version}.war"

    _, _, stderr = client.exec_command(rm_old_cmd)
    error = stderr.read().decode('utf-8')
    if error:
        # Dies nur als Warnung behandeln, da der Deploy an sich erfolgreich war
        print(f"     WARNUNG: Löschen der alten Version '{old_version}' fehlgeschlagen: {error}")
    else:
        print("     Alte .war-Datei erfolgreich gelöscht.")

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

