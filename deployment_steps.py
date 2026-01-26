# Farben definieren
YELLOW = '\033[93m'
GREEN = '\033[92m'  
RED = '\033[91m'
RESET = '\033[0m'

"""Sucht nach einer alten Version der Komponente und gibt die Version zurück."""
def find_old_version(client, komponente, link, isSoapserver):
    
    print("  -> Suche nach alter Version...")
    nav = "cd /opt/wildfly/deploy && "
    
    search_name = ""
    if komponente == "help":
        search_name = "wwshelp"
    else:
        search_name = (link if isSoapserver else komponente)

    get_komp_cmd = nav + "ls " + search_name + "-*" 
    _, stdout, _ = client.exec_command(get_komp_cmd)
    output = stdout.read().decode('utf-8').splitlines()
    
    if output:
        prefix_to_remove = search_name + "-"
        old_version = output[0].replace(prefix_to_remove, "")[:-4]
        print(f"    Alte Version gefunden: {YELLOW}{old_version}{RESET}")
        return old_version
    
    print("    Keine alte Version gefunden.")
    return None
	
"""Lädt die angegebene .war-Datei aus dem Repository herunter."""
def download_war_file(client, komponente, version, link, isSoapserver):
    print("  -> Lade neue .war-Datei herunter...")
    nav = "cd /opt/wildfly/deploy && "

    filename = ""
    url = ""

    if komponente == "wwsreports":
        filename = f"wwsreports-{version}.war"
        url = f"http://wwsrepo.mueller.de/repository/handelsmanagement/wwsreports/{version.split('-')[0]}/{version.split('-')[1]}/{filename}"
    elif komponente == "help":
        filename = f"wwshelp-{version}.war"
        url = f"http://wwsrepo.mueller.de/repository/handelsmanagement/wwshelp/{version.split('-')[0]}/{version.split('-')[1]}/{filename}"
    elif isSoapserver:
        filename = f"{link}-{version}.war"
        url = f"http://wwsrepo.mueller.de/repository/maven-releases/de/mueller/erp/apps/{link}/{version}/{filename}"
    else:
        filename = f"{komponente}-{version}.war"
        url = f"http://wwsrepo.mueller.de/repository/maven-releases/de/mueller/erp/apps/{komponente}/{version}/{filename}"

    wget_cmd = f"wget -O {filename} {url}"

    if komponente != "wwsartdecl":
        _, stdout, stderr = client.exec_command(nav + wget_cmd)
        if stdout.channel.recv_exit_status() != 0:
            raise Exception(f"wget {RED}fehlgeschlagen{RESET}: {stderr.read().decode('utf-8')}")
    print(f"     Download {GREEN}erfolgreich{RESET}.")


"""Führt 'undeploy' auf dem JBoss-Server aus."""
def undeploy_old_version(client, komponente, jboss_conn):    
    print("  -> Undeploy der alten Version...")
    undeploy_cmd = jboss_conn + "undeploy " + komponente + ".war --all-relevant-server-groups'"
    
    for i in range(3):
        _, stdout, stderr = client.exec_command(undeploy_cmd)
        if stdout.channel.recv_exit_status() == 0:
            print(f"     Undeploy {GREEN}erfolgreich{RESET}.")
            return
        else:
            output = stderr.read().decode('utf-8')
            if "timed out" in output:
                print(f"     Undeploy Timeout, {YELLOW}versuche erneut ({i+1}/3)...")
            else:
                raise Exception(f"Undeploy {RED}fehlgeschlagen: {output}")
    raise Exception(f"Undeploy ist nach 3 Versuchen {RED}fehlgeschlagen{RESET}.")


"""Löscht den alten Symlink im Deploy-Verzeichnis."""
def remove_old_symlink(client, komponente):
    print("  -> Lösche alten Symlink...")
    rm_link_cmd = "rm /opt/wildfly/deploy/" + komponente + ".war"
    _, _, stderr = client.exec_command(rm_link_cmd)
    error = stderr.read().decode('utf-8')
    if error and "No such file or directory" not in error:
         raise Exception(f"Löschen des Links {RED}fehlgeschlagen{RESET}: {error}")
    print("     Alter Link gelöscht oder war nicht vorhanden.")


"""Erstellt den neuen Symlink zur neuen .war-Datei."""
def create_new_symlink(client, komponente, version, link, isSoapserver):
    print("  -> Setze neuen Symlink...")
    if komponente == "help":
        new_link_cmd = f"ln -s /opt/wildfly/deploy/wwshelp-{version}.war /opt/wildfly/deploy/{komponente}.war"
    else:
        new_link_cmd = f"ln -s /opt/wildfly/deploy/{link}-{version}.war /opt/wildfly/deploy/{komponente}.war"
    
    _, _, stderr = client.exec_command(new_link_cmd)
    if stderr.read():
        raise Exception(f"Setzen des neuen Links {RED}fehlgeschlagen{RESET}: {stderr.read().decode('utf-8')}")
    print(f"     Neuer Link {GREEN}erfolgreich{RESET} gesetzt.")


"""Führt 'deploy' der neuen Version auf dem JBoss-Server aus."""
def deploy_new_version(client, komponente, jboss_conn):
    print("  -> Deploy der neuen Version...")
    deploy_cmd = jboss_conn + f"deploy /opt/wildfly/deploy/{komponente}.war --name={komponente}.war --runtime-name={komponente}.war --all-server-groups'"
    _, _, stderr = client.exec_command(deploy_cmd)
    if stderr.read():
        raise Exception(f"Deploy der neuen Version {RED}fehlgeschlagen{RESET}: {stderr.read().decode('utf-8')}")
    print(f"     Deploy {GREEN}erfolgreich{RESET}.")


"""Aktualisiert oder fügt die SYSPARAM-Einträge hinzu."""
def update_sysparams(conn, cursor, komponente, version, link, isSoapserver, baen):
    if komponente not in ["wwsreports", "wwsartdecl", "help", "jmxservice"]:
        sysitem_name = (link.upper() if isSoapserver else komponente.upper())
        
        # definieren der Suffix und der Beschreibungstext
        params_to_process = [
            ("MIN", f"Version von {sysitem_name}"),
            ("OPT", f"Optimale Version fuer {sysitem_name}"),
            ("MAX", f"Version von {sysitem_name}")
        ]
        
        sql_commands_to_execute = []

        for suffix, bez_text in params_to_process:
            sysitem = f"VERSION.{sysitem_name}.{suffix}"
            
            cursor.execute(f"SELECT WERT FROM SYSPARAM WHERE SYSITEM = '{sysitem}'")
            if cursor.fetchone():
                # Existiert -> UPDATE
                sql = f"UPDATE SYSPARAM SET WERT = '{version}', DAEN = getdate(), BAEN = {baen} WHERE SYSITEM = '{sysitem}'"
            else:
                # Existiert nicht -> INSERT
                sql = f"INSERT INTO SYSPARAM (SYSITEM, WERT, DAEN, BAEN, BEZ, DAUF, BAUF) VALUES ('{sysitem}', '{version}', getdate(), {baen}, '{bez_text}', getdate(), {baen})"
            
            # Füge den fertigen Befehl zur Liste hinzu
            sql_commands_to_execute.append(sql)

        print ("  -> DB-Status wird aktualisiert...")
        
        for command in sql_commands_to_execute:
            cursor.execute(command)
        
        conn.commit()
        
        print("     DB-Status nach dem Update:")
        get_ver_sql = f"SELECT * FROM SYSPARAM WHERE SYSITEM LIKE 'VERSION.{sysitem_name}.%'"
        cursor.execute(get_ver_sql)
        rows = cursor.fetchall()
        for row in rows:
            print(f"     -> {row}")

    else:
        print("  -> Komponente benötigt kein DB-Update, wird übersprungen.")

"""Löscht die alte .war-Datei vom Server."""
def remove_old_war_file(client, komponente, old_version, link, isSoapserver):
    print("  -> Lösche alte .war-Datei...")
    if komponente == "help":
        rm_old_cmd = f"rm -r /opt/wildfly/deploy/wwshelp-{old_version}.war"
    else:
        rm_old_cmd = f"rm -r /opt/wildfly/deploy/{(link if isSoapserver else komponente)}-{old_version}.war"

    _, _, stderr = client.exec_command(rm_old_cmd)
    error = stderr.read().decode('utf-8')
    if error:
        # Dies nur als Warnung behandeln, da der Deploy an sich erfolgreich war
        print(f"     WARNUNG: Löschen der alten Version '{old_version}' {RED}fehlgeschlagen{RESET}: {error}")
    else:
        print(f"     Alte .war-Datei {GREEN}erfolgreich{RESET} gelöscht.")
