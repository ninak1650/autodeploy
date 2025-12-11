import os
import getpass
import paramiko
import pyodbc
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode

def decrypt_root_password():
    """Entschlüsselt das Root-Passwort mithilfe der 'DB_PASSPHRASE' Umgebungsvariable."""
    try:
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
        return decr_root.decode()
    except KeyError:
        print("FEHLER: Die Umgebungsvariable 'DB_PASSPHRASE' wurde nicht gefunden.")
        return None
    except Exception as e:
        print(f"FEHLER bei der Entschlüsselung des Root-Passworts: {e}")
        return None

def connect_to_database(server, database):
    """Fragt das Sybase-Passwort ab und stellt eine DB-Verbindung zum übergebenen Server her."""
    username = "chensaso"  #saso-Name, anpassen!
    while True:
        sybase_pass = getpass.getpass(prompt=f"Gib das Saso-Passwort für '{username}' auf '{server}' ein: ")
        connection_string = f'DRIVER={{Adaptive Server Enterprise}};SERVER={server};PORT=20000;DATABASE={database};UID={username};PWD={sybase_pass}'
        try:
            conn = pyodbc.connect(connection_string, timeout=5)
            print(f"  -> Datenbankverbindung zu {database}@{server} erfolgreich hergestellt.")
            return conn
        except pyodbc.Error as e:
            if "Login failed" in str(e):
                print("Login fehlgeschlagen. Bitte versuche es erneut.")
            else:
                print(f"Ein unerwarteter DB-Fehler ist aufgetreten: {e}")
                return None

def create_ssh_client():
    """Erstellt und konfiguriert ein SSH-Client-Objekt."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("  -> SSH-Client initialisiert.")
    return client

def perform_authentication(server, database):
    """Führt alle Authentifizierungsschritte für die angegebene Umgebung aus."""
    print(f"Starte Authentifizierungsprozess für: {database}@{server}")
    
    # Ruft connect_to_database mit den Parametern auf
    db_connection = connect_to_database(server, database)
    if not db_connection:
        print("Abbruch: Datenbankverbindung konnte nicht hergestellt werden.")
        return None, None, None

    root_password = decrypt_root_password()
    if not root_password:
        print("Abbruch: Root-Passwort konnte nicht entschlüsselt werden.")
        db_connection.close()
        return None, None, None

    ssh_client = create_ssh_client()
    
    print("Authentifizierung erfolgreich abgeschlossen.\n")
    return ssh_client, db_connection, root_password