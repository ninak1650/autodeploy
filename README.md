Anleitung: Auto-Deploy Skript
1. Code anpassen (für Test & Prod)

In authentifizierung.py: Zeile 38 (saso-username)
In autodeploy_test.py: Zeile 8 (PSNR)
In autodeploy_prod.py: Zeile 8 (PSNR)

2. Umgebung einrichten 
Pakete installieren: pip install pyodbc paramiko cryptography
Passwort für Entschlüsselung(frag Martina): Powershell: $env:DB_PASSPHRASE = " "
                                            cmd: setx DB_PASSPHRASE " "

3. Skript starten und deployen 
Öffne eine neue Kommandozeile (CMD) und zum Verzeichnes navigieren
'python autodeploy_prod.py' oder 'python autodeploy_test.py' ausfuehren