import tkinter as tk
from tkinter import ttk, messagebox
from workflow import deploy_existing_component, deploy_new_component

def start_application(client, conn, decr_root, baen):
    """Erstellt und startet die gesamte GUI-Anwendung."""
    
    cursor = conn.cursor()

    def master_conn(master):
        try:
            client.connect(master, username='root', password=decr_root, look_for_keys=False, allow_agent=False)
            return True
        except Exception as e:
            messagebox.showerror("Verbindungsfehler", f"Konnte keine SSH-Verbindung zu {master} herstellen:\n\n{e}")
            return False

    def java_komp(master):
        try:
            _, stdout, _ = client.exec_command(f"/opt/wildfly/bin/jboss-cli.sh --controller={master}:9999 --user=admin --password=Admin --connect --commands='deploy -l'")
            output = stdout.read().decode('utf-8', errors='ignore').splitlines()
            return [line.partition(".war")[0] for line in output[1:-1] if "jmx.war" not in line]
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Komponenten nicht abrufen: {e}")
            return []

    def update_komponenten(event):
        master = cluster.get()
        if master_conn(master):
            java_komponenten = java_komp(master)
            komponenten.set('')
            input_box.delete(0, tk.END)
            komponenten['values'] = java_komponenten

    def open_new_component_popup(parent, style_font):
        popup = tk.Toplevel(parent)
        popup.title("Neue Komponente deployen")
        popup.resizable(False, False)
        popup.transient(parent)
        
        x = parent.winfo_x() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
        popup.geometry(f"420x200+{x}+{y}")
        
        ttk.Label(popup, text="Cluster:", font=style_font).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        cluster_entry = ttk.Combobox(popup, values=["server690vmx"], width=25, font=style_font)
        cluster_entry.grid(row=0, column=1, padx=12, pady=10, sticky="we")

        ttk.Label(popup, text="Komponente:", font=style_font).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        komponent_entry = ttk.Entry(popup, font=style_font, width=25)
        komponent_entry.grid(row=1, column=1, padx=12, pady=5, sticky="we")

        ttk.Label(popup, text="Version:", font=style_font).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        version_entry = ttk.Entry(popup, font=style_font, width=25)
        version_entry.grid(row=2, column=1, padx=12, pady=5, sticky="we")

        def on_deploy_new():
            deploy_new_component(
                client, decr_root, conn, cursor, baen, 
                komponent_entry.get(), 
                version_entry.get(), 
                cluster_entry.get()
            )
            popup.destroy()

        deploy_btn = ttk.Button(popup, text="Deploy", command=on_deploy_new)
        deploy_btn.grid(row=3, column=1, pady=15, sticky="e", padx=12)

        popup.grab_set()
        parent.wait_window(popup)

    # --- Main Fenster ---
    root = tk.Tk()
    root.title("Wildfly ausliefern")
    root.geometry("420x200")
    root.resizable(False, False)
    global_font = ("Arial", 13)

    style = ttk.Style()
    style.configure("TCombobox", font=global_font)
    style.configure("TLabel", font=global_font)
    root.columnconfigure(1, weight=1)

    lbl_cluster = ttk.Label(root, text="Cluster:")
    lbl_cluster.grid(row=0, column=0, padx=(12, 6), pady=(10, 5), sticky="e")
    cluster = ttk.Combobox(root, values=["server690vmx"], width=30)
    cluster.grid(row=0, column=1, padx=(6, 12), pady=(10, 5), sticky="we")

    lbl_komp = ttk.Label(root, text="Komponente:")
    lbl_komp.grid(row=1, column=0, padx=(12, 6), pady=5, sticky="e")
    komponenten = ttk.Combobox(root, values=[], width=30)
    komponenten.grid(row=1, column=1, padx=(6, 12), pady=5, sticky="we")

    lbl_version = ttk.Label(root, text="Version:")
    lbl_version.grid(row=2, column=0, padx=(12, 6), pady=(5, 12), sticky="e")
    input_box = tk.Entry(root, font=global_font, width=30)
    input_box.grid(row=2, column=1, padx=(6, 12), pady=(5, 12), sticky="we")

    btn_row = ttk.Frame(root)
    btn_row.grid(row=3, column=0, columnspan=2, pady=8)

    update_btn = ttk.Button(btn_row, text="Aktualisieren", 
                            command=lambda: deploy_existing_component(
                                client, decr_root, conn, cursor, baen, 
                                komponenten.get(), 
                                input_box.get(), 
                                cluster.get()
                            ))
    update_btn.pack(side=tk.LEFT, padx=8)

    new_btn = ttk.Button(btn_row, text="Neue Komponente", command=lambda: open_new_component_popup(root, global_font))
    new_btn.pack(side=tk.LEFT, padx=8)
    
    cluster.bind("<<ComboboxSelected>>", update_komponenten)

    # --- GUI starten ---
    root.mainloop()

    print("Schließe Verbindungen...")
    client.close()
    conn.close()
    print("Verbindungen geschlossen. Programm beendet.")

