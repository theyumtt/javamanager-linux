import customtkinter as ctk
import os
import subprocess
import threading
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        self.geometry("400x400")
        self.after(100, self.lift)
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="⚙️ Settings / Ayarlar", font=("Helvetica", 20, "bold")).pack(pady=20)
        
        self.lang_seg = ctk.CTkSegmentedButton(self, values=["TR", "EN"], command=self.parent.change_lang)
        self.lang_seg.set(self.parent.current_lang)
        self.lang_seg.pack(pady=10)

        self.ppa_btn = ctk.CTkButton(self, text="Update Repos (apt update)", command=self.update_repos, fg_color="#34495e")
        self.ppa_btn.pack(pady=10)
        
        ctk.CTkButton(self, text="Close / Kapat", command=self.destroy).pack(pady=20)

    def update_repos(self):
        os.system("x-terminal-emulator -e sudo apt update &")

class JavaManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("JavaManager")
        self.geometry("600x600")
        self.current_lang = "TR"
        
        self.texts = {
            "TR": {"title": "☕ JavaManager", "list": "Kurulu Sürümler", "btn": "Java Kur", "status": "Hazır"},
            "EN": {"title": "☕ JavaManager", "list": "Installed Versions", "btn": "Install Java", "status": "Ready"}
        }

        self.setup_ui()
        self.refresh_installed_javas()

    def setup_ui(self):
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=5)
        self.settings_btn = ctk.CTkButton(self.top_bar, text="⚙️", width=40, command=lambda: SettingsWindow(self))
        self.settings_btn.pack(side="right")

        self.main_label = ctk.CTkLabel(self, text=self.texts[self.current_lang]["title"], font=("Helvetica", 26, "bold"))
        self.main_label.pack(pady=10)

        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        self.list_title = ctk.CTkLabel(self.list_frame, text=self.texts[self.current_lang]["list"], font=("Helvetica", 14, "bold"))
        self.list_title.pack(pady=5)
        
        self.installed_list = ctk.CTkTextbox(self.list_frame, height=150, font=("Helvetica", 14))
        self.installed_list.pack(pady=10, padx=15, fill="both", expand=True)

        self.opt_frame = ctk.CTkFrame(self)
        self.opt_frame.pack(pady=10, padx=20, fill="x")
        self.version_combo = ctk.CTkComboBox(self.opt_frame, values=["21", "17", "11", "8"])
        self.version_combo.grid(row=0, column=0, padx=20, pady=10); self.version_combo.set("21")
        
        self.type_var = ctk.StringVar(value="jdk")
        ctk.CTkRadioButton(self.opt_frame, text="JDK", variable=self.type_var, value="jdk").grid(row=0, column=1, padx=10)
        ctk.CTkRadioButton(self.opt_frame, text="JRE", variable=self.type_var, value="jre").grid(row=0, column=2, padx=10)

        self.install_btn = ctk.CTkButton(self, text=self.texts[self.current_lang]["btn"], command=self.start_system_install, height=50, font=("Helvetica", 16, "bold"), fg_color="#27ae60")
        self.install_btn.pack(pady=20)
        self.status_label = ctk.CTkLabel(self, text=self.texts[self.current_lang]["status"], text_color="gray")
        self.status_label.pack(pady=5)

    def clean_name(self, raw):
        """Karmaşık isimleri (java-1.17.0-openjdk...) temizleyip 'Java X' yapar."""
        if "default" in raw.lower(): return None
        
        # Versiyon numarasını bul (8, 11, 17, 21 gibi)
        match = re.search(r'(?:1\.)?(\d+)', raw)
        if match:
            ver_num = match.group(1)
            prefix = "OpenJDK" if "openjdk" in raw.lower() else "Java"
            return f"☕ {prefix} {ver_num}"
        return raw

    def refresh_installed_javas(self):
        self.installed_list.configure(state="normal")
        self.installed_list.delete("0.0", "end")
        
        found_set = set()
        jvm_path = "/usr/lib/jvm"
        
        if os.path.exists(jvm_path):
            for folder in os.listdir(jvm_path):
                # Sadece gerçek dizinleri ve içindeki java binary'sini kontrol et
                if os.path.isdir(os.path.join(jvm_path, folder)):
                    clean = self.clean_name(folder)
                    if clean:
                        found_set.add(clean)
        
        if not found_set:
            self.installed_list.insert("0.0", "Java not found.")
        else:
            # Sürümleri sıralı göster
            sorted_list = sorted(list(found_set), key=lambda x: int(re.search(r'\d+', x).group()), reverse=True)
            self.installed_list.insert("0.0", "\n".join(sorted_list))
            
        self.installed_list.configure(state="disabled")

    def change_lang(self, choice):
        self.current_lang = choice
        self.main_label.configure(text=self.texts[choice]["title"])
        self.list_title.configure(text=self.texts[choice]["list"])
        self.install_btn.configure(text=self.texts[choice]["btn"])
        self.status_label.configure(text=self.texts[choice]["status"])

    def start_system_install(self):
        v = self.version_combo.get()
        pkg = f"openjdk-{v}-{self.type_var.get()}"
        cmd = f"sudo apt install {pkg} -y"
        os.system(f"x-terminal-emulator -e bash -c '{cmd}; read' &")
        threading.Timer(10.0, self.refresh_installed_javas).start()

if __name__ == "__main__":
    app = JavaManager()
    app.mainloop()
