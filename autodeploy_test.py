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
username = ""  
baen = "-"
database = "wwst3"  #database = "wwstp"  
while(enter_pass):
    sybase_pass = getpass.getpass(prompt="Enter your sybase password: ")
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

        

def deployKomp():
    version = input_box.get()
    komponente = komponenten.get()
    isSoapserver = False
    if(komponente == ""):
        messagebox.showwarning("Warning", "Wähle eine Komponente aus!")
        return
    if(version != ""):
        if(komponente == "wws" or komponente == "wwsartdecl"):
            isSoapserver = True
            link = "soapserver"
        try:
            nav = "cd /opt/wildfly/deploy && "
            isOldavailable = True
            if(komponente == "help"):
                get_komp = nav + "ls wwshelp-*"
            else:
                get_komp = nav + "ls " + (link if isSoapserver else komponente) + "-*"
            nill, stdout, stderr = client.exec_command(get_komp)
            output = stdout.read().decode('utf-8', errors='ignore').splitlines()
            if(output):
                if(komponente == "help"):
                    old_version = output[0].replace("wwshelp-", "")[:-4]
                else:
                    old_version = output[0].replace((link if isSoapserver else komponente) + "-", "")[:-4]
                print("Old version: " + old_version)
            else:
                print("No old version found")
                isOldavailable = False

            jboss_conn = "/opt/wildfly/bin/jboss-cli.sh --controller=" + cluster.get() + ":9999 --user=admin --password=Admin --connect --commands='"

            if(komponente == "wwsreports"):
                wget = "wget http://wwsrepo.mueller.de/repository/handelsmanagement/wwsreports/" + version.split("-")[0] + "/" + version.split("-")[1] + "/wwsreports-" + version + ".war"
            elif(komponente == "help"):
                wget = "wget http://wwsrepo.mueller.de/repository/handelsmanagement/wwshelp/" + version.split("-")[0] + "/" + version.split("-")[1] + "/wwshelp-" + version + ".war"
            elif(isSoapserver):
                wget = "wget http://wwsrepo.mueller.de/repository/maven-releases/de/mueller/erp/apps/" + link +"/" + version + "/" + link + "-" + version +".war"
            else:
                wget = "wget http://wwsrepo.mueller.de/repository/maven-releases/de/mueller/erp/apps/" + komponente +"/" + version + "/" + komponente + "-" + version +".war"
            if(komponente != "wwsartdecl"):
                nill, stdout, stderr = client.exec_command(nav + wget)
                exit_status = stdout.channel.recv_exit_status()
                lines = stderr.read().decode('utf-8').splitlines()
                if(exit_status):
                    match = next((line for line in lines if "ERROR 404: Not Found" in line), None)
                    if match:
                        print(match)
                        messagebox.showwarning("Warning", "Der link ist nicht greifbar, ist die gennante Version korrekt?")
                        return
                else:
                    match = next((line for line in lines if "saved" in line), None)
                    if match:
                        print(match)

            retry_cnt = 0
            undeploy = jboss_conn + "undeploy " + komponente + ".war" + " --all-relevant-server-groups'"
            while(retry_cnt <= 3):
                print("Undeploying...")
                nill, stdout, stderr = client.exec_command(undeploy)
                output = stdout.read().decode("utf-8")
                error = stderr.read().decode('utf-8')
                exit_status = stdout.channel.recv_exit_status()
                if(exit_status):
                    if "timed out after" in output:
                        retry_cnt += 1
                        print("Undeploy timeout, trying again")
                    else:
                        print("Undeploy failed: " + output)
                        retry_cnt = 4
                else:
                    retry_cnt = 5
            if retry_cnt == 4:
                raise Exception("Undeploy failed")
            elif retry_cnt == 5:
                print("Undeploy done")

            check_undeploy = "deploy -l"
            nill, stdout, stderr = client.exec_command( jboss_conn + check_undeploy + "'" )
            output = stdout.read().decode('utf-8', errors='ignore')
            if((komponente + ".war") in output):
                print("Undeploy failed")
                raise Exception("Undeploy failed")
            else:
                print("Undeployed successfully")

            link_del = "rm /opt/wildfly/deploy/" + komponente + ".war"
            nill, stdout, stderr = client.exec_command(link_del)
            exit_status = stdout.channel.recv_exit_status()
            if(exit_status):
                error = stderr.read().decode('utf-8')
                if "No such file or directory" in error:
                    print ("No link set, skipping old link deletion")
                else:
                    print("Old link deletion failed: " + error)
                    raise Exception("Old link deletion failed")
            else:
                print("Old link deletion done")

            if(komponente == "help"):
                new_link = "ln -s /opt/wildfly/deploy/wwshelp-" + version + ".war /opt/wildfly/deploy/" + komponente + ".war"
            else:
                new_link = "ln -s /opt/wildfly/deploy/" + (link if isSoapserver else komponente) + "-" + version + ".war /opt/wildfly/deploy/" + komponente + ".war"
            nill, stdout, stderr = client.exec_command(new_link)
            exit_status = stdout.channel.recv_exit_status()
            if(exit_status):
                print("Setting new link failed: " + stderr.read().decode('utf-8'))
                raise Exception("Setting new link failed")
            else:
                print("Setting new link done")

            #DB Update:
            if(komponente != "wwsreports" and komponente != "wwsartdecl" and komponente != "help" and komponente != "jmxservice"):
                set_min = "update SYSPARAM set WERT = '" + version + "', DAEN = getdate(), BAEN = " + baen + " where SYSITEM = 'VERSION." + (link.upper() if isSoapserver else komponente.upper()) + ".MIN'"
                set_opt = "update SYSPARAM set WERT = '" + version + "', DAEN = getdate(), BAEN = " + baen + " where SYSITEM = 'VERSION." + (link.upper() if isSoapserver else komponente.upper()) + ".OPT'"
                get_ver = "select * from SYSPARAM where SYSITEM like 'VERSION." + (link.upper() if isSoapserver else komponente.upper()) + ".%'"
                print ("DB updates: ")
                cursor.execute(set_min)
                cursor.execute(set_opt)
                conn.commit()
                cursor.execute(get_ver)
                rows = cursor.fetchall()
                for row in rows:
                    print(row)

            deploy = jboss_conn + "deploy /opt/wildfly/deploy/" + komponente + ".war  --name=" + komponente + ".war --runtime-name=" + komponente + ".war --all-server-groups'"
            nill, stdout, stderr = client.exec_command(deploy)
            exit_status = stdout.channel.recv_exit_status()
            if(exit_status):
                print("Deploy filed: " + stderr.read().decode('utf-8'))
                raise Exception("Deploy failed")
            else:
                print("Deploy done")

            ##ALTE VERSION LÖSCHEN
            if(komponente != "wwsartdecl" and isOldavailable):
                if(komponente == "help"):
                    rm_old = "rm -r /opt/wildfly/deploy/wwshelp-" + old_version + ".war"
                else:
                    rm_old = "rm -r /opt/wildfly/deploy/" + (link if isSoapserver else komponente) + "-" + old_version + ".war"
                nill, stdout, stderr = client.exec_command(rm_old)
                exit_status = stdout.channel.recv_exit_status()
                if(exit_status):    
                    print("Removing old version failed" + stderr.read().decode('utf-8'))
                    raise Exception("Removing old version failed")
                else:
                    print("Removing old version done")
            elif(not isOldavailable):
                print("Skipping removing old version, no old Version found")


            komponenten.set('')
            input_box.delete(0, tk.END)
            messagebox.showinfo("Info", "Deploy erfolgreich.")

        except Exception as e:
            print(f"An error occurred: {e}")
            messagebox.showwarning("Warning", "Oops! Etwas ist schiefgelaufen.")

    else:
        messagebox.showwarning("Warning", "Gib eine Version ein!")

# Create the main window

root = tk.Tk()
root.title("Wildfly ausliefern")
root.geometry("300x200")
root.resizable(False, False)

global_font = ("Arial", 13) 
style = ttk.Style()
style.configure("TCombobox", font=global_font)
style.configure("TLabel",    font=global_font)  
style.configure("TCombobox", font=global_font)

cluster = ttk.Combobox(root, values=["server690vmx"], width=30) #["server320vmx", "server662vmx", "server3061vmx", "server3161vmx", "server3261vmx"]
cluster.grid(row=0, column=0, padx=10, pady=5)


komponenten = ttk.Combobox(root, values=[], width=30)
komponenten.grid(row=1, column=0, padx=10, pady=5)


input_box = tk.Entry(root, font=global_font, width=30)
input_box.grid(row=2, column=0, padx=10, pady=20)

deploy_btn = ttk.Button(root, text="Deploy", command=deployKomp)
deploy_btn.grid(row=3, column=0, padx=20,pady=10)


cluster.bind("<<ComboboxSelected>>", update_komponenten)

# Start the GUI
root.mainloop()

client.close()
conn.close()