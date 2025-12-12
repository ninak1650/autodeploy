Autodeploy von Wildfly Komponenten
Für ein detailliertes Verständnis der Projektarchitektur und wie die einzelnen Skripte zusammenarbeiten, siehe die Datei **INFO.md**.

🔧 Vorbereitung

1. Code anpassen (für Test & Prod)

-In authentifizierung.py: Zeile 38 (saso-username)

-In autodeploy_test.py: Zeile 8 (PSNR)

-In autodeploy_prod.py: Zeile 8 (PSNR)

2. Umgebungsvariable setzen
Die Umgebungsvariable DB_PASSPHRASE muss definiert werden.
➡️ Martina fragen für den korrekten Wert.

-Powershell: $env:DB_PASSPHRASE = " "

-cmd: setx DB_PASSPHRASE " "

3. Command Prompt öffnen
Öffne eine cmd (oder PowerShell) und navigiere in das Projektverzeichnis.

4. Benötigte Python-Bibliotheken installieren
Führe folgende Befehle aus:

pip3 install cryptography
pip3 install paramiko
pip3 install pyodbc


5. Skripte ausführen

python autodeploy_test.py
python autodeploy_prod.py



🛠️ Fehlerbehebung (Troubleshooting)

🔹 1. Umgebungsvariablen prüfen
Stelle sicher, dass der PATH-Eintrag Folgendes enthält:

C:\was\auch\immer\Python\Python313\Scripts\



🔹 2. Falls python nicht gefunden wird
Manuell Alias setzen (PowerShell):

Set-Alias python "C:\Pfad\zum\Python\python.exe"



🔹 3. Probleme bei Bibliotheken
Wenn Python-Pakete fehlen, diese installieren:

pip3 install <paketname>


Falls die Firewall pip blockiert:
➡️ Auf externem Netzwerk installieren (z. B. Mobile Daten oder im Home-Office).