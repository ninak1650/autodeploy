Die Architektur: 

1. autodeploy_test.py / autodeploy_prod.py 

Die Start-Skripte der Anwendung. Das sind die einzigen Dateien, die du jemals direkt ausführst.

Definieren die umgebungsspezifische Konfiguration (Server, Datenbank, BAEN) für TEST bzw. PROD. Sie initiieren den Authentifizierungsprozess und starten die GUI.

Unterschied: Test Port=/ Prod Port=

2. authentifizierung.py 
Passwörter prüfen und Zugang verschaffen.

3. GUI.py 
Definiert die gesamte grafische Benutzeroberfläche.

4. workflow.py (Prozess-Steuerung)
Enthält die beiden Hauptprozesse: deploy_existing_component und deploy_new_component. 
Definiert die logische Abfolge der Arbeitsschritte, indem sie die Funktionen aus deployment_steps.py aufruft.

5. deployment_steps.py (Deployment-Schritte)
Beinhaltet alle Funktionen,  die die Bausteine für die in workflow.py definierten Prozesse bilden.
