import os
import sys
import msvcrt  
import paramiko
import pyodbc
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode
from colorama import init

# Damit es mit CMD und WindowsPS funktioniert
init()

# Farben
CYAN = '\033[96m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

# SaSo user
username = ""

def getpass_colored(prompt="Password: ", mask="*", color=""):
    """Liest ein Passwort von der Konsole und zeigt eine farbige Maske an."""
    password = ""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    
    while True:
        char_byte = msvcrt.getch()
        if char_byte in (b'\r', b'\n'):
            sys.stdout.write('\n')
            sys.stdout.flush()
            break
        elif char_byte == b'\x08':
            if len(password) > 0:
                password = password[:-1]
                sys.stdout.write('\b \b')
                sys.stdout.flush()
        else:
            try:
                char = char_byte.decode('utf-8')
                password += char
                sys.stdout.write(f"{color}{mask}{RESET}")
                sys.stdout.flush()
            except UnicodeDecodeError:
                pass 
    return password

def decrypt_root_password():
    """Entschlüsselt das Root-Passwort."""
    try:
        encr_root = "gAAAAABoEfMBo7LMVNeSN5YWJ3L2P3B7EARh3_EUJd7f0cIWKxGBki0AJmMEzPWMcQxTBRjiXd2rIXEQmnGDQtdg1MKOOTGZobdyZnsUG8hoVjEy0GpWQYQ="
        salt = b"UIy4SDkwW9a6gQkUrjXDBg=="
        passphrase = os.environ["DB_PASSPHRASE"].encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=urlsafe_b64decode(salt),
            iterations=100_000, backend=default_backend()
        )
        key = urlsafe_b64encode(kdf.derive(passphrase))
        fernet = Fernet(key)
        decr_root = fernet.decrypt(encr_root.encode())
        return decr_root.decode()
    except KeyError:
        print(f"{RED}FEHLER: Die Umgebungsvariable 'DB_PASSPHRASE' wurde nicht gefunden.{RESET}")
        return None
    except Exception as e:
        print(f"{RED}FEHLER bei der Entschlüsselung des Root-Passworts: {e}{RESET}")
        return None

def connect_to_database(server, database, port):
    """Fragt das Sybase-Passwort ab und stellt eine DB-Verbindung her."""
    while True:
        prompt_text = (
            f"Gib das Sybase-Passwort für {YELLOW}'{username}'{RESET} "
            f"auf {CYAN}'{server}'{RESET} ein: "
        )
        
        sybase_pass = getpass_colored(prompt=prompt_text, mask='*', color=CYAN)
        connection_string = f'DRIVER={{Adaptive Server Enterprise}};SERVER={server};PORT={port};DATABASE={database};UID={username};PWD={sybase_pass}'
        
        try:
            conn = pyodbc.connect(connection_string, timeout=5)
            print(f"  -> Datenbankverbindung zu {database}@{server}:{port} {GREEN}erfolgreich hergestellt.{RESET}")
            return conn
        except pyodbc.Error as e:
            if "Login failed" in str(e):
                print(f"{RED}Login fehlgeschlagen.{RESET} Bitte versuche es erneut.")
            else:
                print(f"Ein unerwarteter {RED}DB-Fehler{RESET} ist aufgetreten: {e}")
                return None

def create_ssh_client():
    """Erstellt und konfiguriert ein SSH-Client-Objekt."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("  -> SSH-Client initialisiert.")
    return client

def perform_authentication(server, database, port):
    """Führt alle Authentifizierungsschritte aus."""
    print(f"Starte Authentifizierungsprozess für: {CYAN}{database}@{server}{RESET}")
    
    db_connection = connect_to_database(server, database, port)
    if not db_connection:
        print(f"{RED}Abbruch{RESET}: Datenbankverbindung konnte nicht hergestellt werden.")
        return None, None, None

    root_password = decrypt_root_password()
    if not root_password:
        print(f"{RED}Abbruch{RESET}: Root-Passwort konnte nicht entschlüsselt werden.")
        db_connection.close()
        return None, None, None

    ssh_client = create_ssh_client()
    
    print(f"Authentifizierung {GREEN}erfolgreich abgeschlossen.{RESET}\n")
    return ssh_client, db_connection, root_password
