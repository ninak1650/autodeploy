# Autodeploy von Wildfly Komponenten

### 🔧 Vorbereitung
#### 1. Zeilen 18 und 19 anpassen
Passe die entsprechenden Zeilen im Skript gemäß den Anforderungen an.

#### 2. Umgebungsvariable setzen
Die Umgebungsvariable DB_PASSPHRASE muss definiert werden.
➡️ Martina fragen für den korrekten Wert.

#### 3. Command Prompt öffnen
Öffne eine cmd (oder PowerShell) und navigiere in das Projektverzeichnis.

#### 4. Benötigte Python-Bibliotheken installieren
Führe folgende Befehle aus:

```python
pip3 install cryptography
pip3 install paramiko
pip3 install pyodbc
```

#### 5. Skripte ausführen
```python
python autodeploy_test.py
python autodeploy_prod.py
```

### 🛠 Fehlerbehebung (Troubleshooting)
#### 🔹 1. Umgebungsvariablen prüfen
Stelle sicher, dass der PATH-Eintrag Folgendes enthält:
```cmd
C:\was\auch\immer\Python\Python313\Scripts\
```

#### 🔹 2. Falls python nicht gefunden wird
Manuell Alias setzen (PowerShell):
```cmd
Set-Alias python "C:\Pfad\zum\Python\python.exe"
```

#### 🔹 3. Probleme bei Bibliotheken
Wenn Python-Pakete fehlen, diese installieren:
```python
pip3 install <paketname>
```
Falls die Firewall pip blockiert:
➡️ Auf externem Netzwerk installieren (z. B. Mobile Daten oder im Home-Office).