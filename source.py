"""
JavaManager v5.4
─ Kurulu sürümler listesi düzeltildi
─ Dil değişimi tüm widgetlara yansıtıldı
─ Güncelleme kontrolü (depoda yeni sürüm var mı?)
─ Seçilebilir & indirilebilir renk paletleri
─ Paletler ~/.config/javamanager/ altına kaydedilir
"""

import customtkinter as ctk
import os, subprocess, threading, re, shutil, tempfile, json
import urllib.request, urllib.error

# ── Sabitler ──────────────────────────────────────────────────────────────────

CONFIG_DIR   = os.path.expanduser("~/.config/javamanager")
THEME_FILE   = os.path.join(CONFIG_DIR, "theme.json")
APP_VERSION  = "v5.4"
GITHUB_REPO  = "theyumtt/javamanager-linux"
GITHUB_API   = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

# ── Yerleşik Paletler ─────────────────────────────────────────────────────────

PALETTES = {
    "Midnight Blue": {
        "bg":         "#0f1117",
        "surface":    "#161b25",
        "surface2":   "#1c2333",
        "border":     "#242d3d",
        "accent":     "#3b82f6",
        "accent_dim": "#1d3a6b",
        "accent_hover":"#2563eb",
        "green":      "#22c55e",
        "green_dim":  "#14532d",
        "red":        "#ef4444",
        "red_dim":    "#7f1d1d",
        "text":       "#e2e8f0",
        "muted":      "#64748b",
        "active":     "#38bdf8",
        "row_def":    "#1c2740",
    },
    "Forest": {
        "bg":         "#0d1410",
        "surface":    "#141f18",
        "surface2":   "#1a2920",
        "border":     "#243328",
        "accent":     "#4ade80",
        "accent_dim": "#14532d",
        "accent_hover":"#22c55e",
        "green":      "#86efac",
        "green_dim":  "#166534",
        "red":        "#f87171",
        "red_dim":    "#7f1d1d",
        "text":       "#ecfdf5",
        "muted":      "#6b7280",
        "active":     "#86efac",
        "row_def":    "#152b1e",
    },
    "Rose Noir": {
        "bg":         "#130d12",
        "surface":    "#1e1320",
        "surface2":   "#261929",
        "border":     "#362240",
        "accent":     "#e879f9",
        "accent_dim": "#701a75",
        "accent_hover":"#d946ef",
        "green":      "#a78bfa",
        "green_dim":  "#3b0764",
        "red":        "#fb7185",
        "red_dim":    "#881337",
        "text":       "#fdf4ff",
        "muted":      "#a1a1aa",
        "active":     "#f0abfc",
        "row_def":    "#2a1630",
    },
    "Amber": {
        "bg":         "#0f0e09",
        "surface":    "#1a1810",
        "surface2":   "#242116",
        "border":     "#352f1e",
        "accent":     "#f59e0b",
        "accent_dim": "#78350f",
        "accent_hover":"#d97706",
        "green":      "#84cc16",
        "green_dim":  "#3f6212",
        "red":        "#f87171",
        "red_dim":    "#7f1d1d",
        "text":       "#fefce8",
        "muted":      "#a8a29e",
        "active":     "#fcd34d",
        "row_def":    "#241d0a",
    },
    "Ice": {
        "bg":         "#09111f",
        "surface":    "#0f1e35",
        "surface2":   "#152640",
        "border":     "#1e3454",
        "accent":     "#67e8f9",
        "accent_dim": "#164e63",
        "accent_hover":"#22d3ee",
        "green":      "#34d399",
        "green_dim":  "#065f46",
        "red":        "#f87171",
        "red_dim":    "#7f1d1d",
        "text":       "#e0f2fe",
        "muted":      "#64748b",
        "active":     "#a5f3fc",
        "row_def":    "#102032",
    },
}

# Aktif paleti yükle
def load_theme():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(THEME_FILE):
        try:
            with open(THEME_FILE) as f:
                data = json.load(f)
            name = data.get("name", "Midnight Blue")
            if name in PALETTES:
                return name, PALETTES[name].copy()
            # Özel palet
            if "colors" in data:
                return name, data["colors"]
        except Exception:
            pass
    return "Midnight Blue", PALETTES["Midnight Blue"].copy()

def check_github_update():
    """
    GitHub'daki en son release tag'ini çeker.
    Returns: (latest_tag: str, has_update: bool, release_url: str)
    Hata olursa (None, False, "")
    """
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": f"JavaManager/{APP_VERSION}"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        latest = data.get("tag_name", "")
        url    = data.get("html_url", RELEASES_URL)
        # Sürüm karşılaştırması: sayısal kısmı al
        def ver_tuple(s):
            nums = re.findall(r'\d+', s)
            return tuple(int(x) for x in nums)
        has_update = bool(latest) and ver_tuple(latest) > ver_tuple(APP_VERSION)
        return latest, has_update, url
    except Exception:
        return None, False, ""

def save_theme(name, colors=None):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    payload = {"name": name}
    if colors:
        payload["colors"] = colors
    with open(THEME_FILE, "w") as f:
        json.dump(payload, f, indent=2)

def export_palette(name, colors, path):
    with open(path, "w") as f:
        json.dump({"name": name, "colors": colors}, f, indent=2)

# ── Global renk nesnesi ───────────────────────────────────────────────────────
_theme_name, C = load_theme()

# ── Metinler ──────────────────────────────────────────────────────────────────

TEXTS = {
    "TR": {
        "title":        "JavaManager",
        "installed":    "Kurulu Sürümler",
        "install_btn":  "Kur",
        "ready":        "Hazır",
        "set_def":      "Varsayılan",
        "remove":       "Kaldır",
        "refresh":      "Yenile",
        "no_java":      "Kurulu Java bulunamadı.",
        "active":       "Aktif Sürüm",
        "none":         "—",
        "done":         "Tamamlandı.",
        "installing":   "Kuruluyor…",
        "removing":     "Kaldırılıyor…",
        "setting":      "Ayarlanıyor…",
        "update_repos": "Depoları Güncelle",
        "check_update": "Güncelleme Kontrol Et",
        "checking":     "Kontrol ediliyor…",
        "up_to_date":   "Güncel ✓",
        "update_avail": "Güncelleme mevcut",
        "close":        "Kapat",
        "no_term":      "Terminal bulunamadı!",
        "no_pm":        "Paket yöneticisi yok!",
        "scanning":     "Taranıyor…",
        "version":      "Sürüm",
        "settings":     "Ayarlar",
        "language":     "Dil / Language",
        "system_info":  "Sistem Bilgisi",
        "pkg_mgr":      "Paket Yöneticisi",
        "terminal":     "Terminal",
        "palettes":     "Renk Paletleri",
        "export_pal":   "Paleti Dışa Aktar",
        "import_pal":   "Palet İçe Aktar",
        "restart_note": "Palet için uygulamayı yeniden başlat",
        "update_title": "Güncelleme Kontrolü",
        "app_update":   "Yeni sürüm mevcut",
        "app_current":  "Güncel sürüm",
        "download":     "İndir",
    },
    "EN": {
        "title":        "JavaManager",
        "installed":    "Installed Versions",
        "install_btn":  "Install",
        "ready":        "Ready",
        "set_def":      "Set Default",
        "remove":       "Remove",
        "refresh":      "Refresh",
        "no_java":      "No Java installation found.",
        "active":       "Active Version",
        "none":         "—",
        "done":         "Done.",
        "installing":   "Installing…",
        "removing":     "Removing…",
        "setting":      "Setting default…",
        "update_repos": "Update Repos",
        "check_update": "Check for Updates",
        "checking":     "Checking…",
        "up_to_date":   "Up to date ✓",
        "update_avail": "Update available",
        "close":        "Close",
        "no_term":      "No terminal found!",
        "no_pm":        "No package manager!",
        "scanning":     "Scanning…",
        "version":      "Version",
        "settings":     "Settings",
        "language":     "Language / Dil",
        "system_info":  "System Info",
        "pkg_mgr":      "Package Manager",
        "terminal":     "Terminal",
        "palettes":     "Color Palettes",
        "export_pal":   "Export Palette",
        "import_pal":   "Import Palette",
        "restart_note": "Restart app to apply palette",
        "update_title": "Update Check",
        "app_update":   "New version available",
        "app_current":  "Up to date",
        "download":     "Download",
    },
}

# ── Sistem Algılama ───────────────────────────────────────────────────────────

def detect_pkg_manager():
    for pm in ["pacman", "apt", "dnf", "zypper"]:
        if shutil.which(pm): return pm
    return None

def detect_terminal():
    for t in ["konsole","alacritty","kitty","gnome-terminal",
              "xfce4-terminal","mate-terminal","tilix","xterm","x-terminal-emulator"]:
        if shutil.which(t): return t
    return None

def run_in_terminal(terminal, cmd):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write("#!/bin/bash\n")
        f.write(f"{cmd}\n")
        f.write('echo\necho "─── Bitti / Done. Enter ile kapat ───"\nread\n')
        script = f.name
    os.chmod(script, 0o755)
    launchers = {
        "konsole":             f"konsole -e bash {script}",
        "alacritty":           f"alacritty -e bash {script}",
        "kitty":               f"kitty -- bash {script}",
        "gnome-terminal":      f"gnome-terminal -- bash {script}",
        "xfce4-terminal":      f"xfce4-terminal -e 'bash {script}'",
        "mate-terminal":       f"mate-terminal -e 'bash {script}'",
        "tilix":               f"tilix -e bash {script}",
        "xterm":               f"xterm -e bash {script}",
        "x-terminal-emulator": f"x-terminal-emulator -e bash {script}",
    }
    os.system(launchers.get(terminal, f"bash {script}") + " &")

# ── Paket Komutları ───────────────────────────────────────────────────────────

def build_install_cmd(version, jtype, pm):
    if pm == "pacman":
        pkg = f"jdk{version}-openjdk" if jtype == "jdk" else f"jre{version}-openjdk"
        aur = next((x for x in ["yay","paru"] if shutil.which(x)), None)
        return f"{aur} -S {pkg} --noconfirm" if aur else f"sudo pacman -S {pkg} --noconfirm"
    elif pm == "apt":
        return f"sudo apt install openjdk-{version}-{jtype} -y"
    elif pm == "dnf":
        pkg = f"java-{version}-openjdk" if jtype == "jre" else f"java-{version}-openjdk-devel"
        return f"sudo dnf install {pkg} -y"
    elif pm == "zypper":
        return f"sudo zypper install java-{version}-openjdk"
    return ""

def build_remove_cmd(folder, pm):
    m = re.search(r'(\d+)', folder)
    if not m: return ""
    ver = m.group(1)
    if pm == "pacman":
        return (f"sudo pacman -R jdk{ver}-openjdk --noconfirm 2>/dev/null; "
                f"sudo pacman -R jre{ver}-openjdk --noconfirm 2>/dev/null; true")
    elif pm == "apt":
        return f"sudo apt remove openjdk-{ver}-jdk openjdk-{ver}-jre -y"
    elif pm == "dnf":
        return f"sudo dnf remove java-{ver}-openjdk java-{ver}-openjdk-devel -y"
    return ""

def build_set_default_cmd(folder, pm):
    if pm == "pacman" and shutil.which("archlinux-java"):
        return f"sudo archlinux-java set {folder}"
    elif pm == "apt":
        return f"sudo update-alternatives --set java /usr/lib/jvm/{folder}/bin/java"
    return ""

# ── Java Tarama ───────────────────────────────────────────────────────────────

def scan_javas(pm):
    results = []
    if pm == "pacman" and shutil.which("archlinux-java"):
        try:
            out = subprocess.check_output(
                ["archlinux-java","status"], stderr=subprocess.DEVNULL, text=True
            )
            for line in out.splitlines():
                s = line.strip()
                if not s or "Available" in s or "No Java" in s: continue
                is_def = "(default)" in s
                folder = s.replace("(default)","").strip()
                m = re.search(r'(\d+)', folder)
                ver = m.group(1) if m else folder
                results.append((f"OpenJDK {ver}", folder, is_def))
            if results:
                results.sort(key=lambda x: int(re.search(r'\d+', x[0]).group()), reverse=True)
                return results
        except Exception:
            pass

    jvm = "/usr/lib/jvm"
    if not os.path.exists(jvm): return []
    current = None
    try:
        link = subprocess.check_output(
            ["readlink","-f","/usr/bin/java"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        m = re.search(r'/usr/lib/jvm/([^/]+)/', link)
        if m: current = m.group(1)
    except Exception:
        pass

    seen = set()
    for folder in sorted(os.listdir(jvm)):
        full = os.path.join(jvm, folder)
        if not os.path.isdir(full) or "default" in folder.lower(): continue
        if not os.path.exists(os.path.join(full,"bin","java")): continue
        m = re.search(r'(\d+)', folder)
        if not m: continue
        ver = m.group(1)
        if ver in seen: continue
        seen.add(ver)
        prefix = "OpenJDK" if "openjdk" in folder.lower() else "Java"
        results.append((f"{prefix} {ver}", folder, folder == current))

    results.sort(key=lambda x: int(re.search(r'\d+', x[0]).group()), reverse=True)
    return results

# ── Güncelleme Kontrolü ───────────────────────────────────────────────────────

def check_updates_for(installed_folders, pm):
    """
    Kurulu Java paketleri için depoda güncelleme var mı kontrol eder.
    Returns: list of (display_name, has_update: bool, latest_ver: str)
    """
    results = []
    for display, folder, is_def in installed_folders:
        m = re.search(r'(\d+)', folder)
        if not m:
            results.append((display, False, "?")); continue
        ver = m.group(1)
        has_update = False
        latest = ver

        try:
            if pm == "pacman":
                pkg = f"jdk{ver}-openjdk"
                out = subprocess.check_output(
                    ["pacman","-Qu", pkg], stderr=subprocess.DEVNULL, text=True
                )
                has_update = bool(out.strip())
                # Yeni sürümü parse et
                m2 = re.search(r'->\s*(\S+)', out)
                if m2: latest = m2.group(1)

            elif pm == "apt":
                pkg = f"openjdk-{ver}-jdk"
                out = subprocess.check_output(
                    ["apt-get","--just-print","upgrade"], stderr=subprocess.DEVNULL, text=True
                )
                has_update = pkg in out

            elif pm == "dnf":
                pkg = f"java-{ver}-openjdk"
                out = subprocess.check_output(
                    ["dnf","check-update", pkg], stderr=subprocess.DEVNULL, text=True
                )
                has_update = bool(out.strip()) and "No packages" not in out
        except Exception:
            pass

        results.append((display, has_update, latest))
    return results

# ── Yardımcılar ───────────────────────────────────────────────────────────────

def make_divider(parent):
    f = ctk.CTkFrame(parent, height=1, fg_color=C["border"])
    f.pack(fill="x", padx=20, pady=0)
    return f

# ── Ayarlar Penceresi ─────────────────────────────────────────────────────────

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(app.t("settings"))
        self.geometry("440x560")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.after(120, self.lift)
        self.attributes("-topmost", True)
        self._build()

    def _build(self):
        app = self.app

        # Başlık
        ctk.CTkLabel(self, text=app.t("settings"),
                     font=("Helvetica", 20, "bold"), text_color=C["text"]).pack(pady=(24,4))
        make_divider(self)

        # ── Dil ──────────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text=app.t("language"),
                     font=("Helvetica", 11, "bold"), text_color=C["muted"]).pack(pady=(14,4))
        self.lang_seg = ctk.CTkSegmentedButton(
            self, values=["TR","EN"], command=app.change_lang,
            font=("Helvetica", 13, "bold"),
            fg_color=C["surface2"], selected_color=C["accent"],
            selected_hover_color=C["accent_hover"],
            unselected_color=C["surface2"],
        )
        self.lang_seg.set(app.lang)
        self.lang_seg.pack(pady=4)

        make_divider(self)

        # ── Sistem Bilgisi ────────────────────────────────────────────────────
        ctk.CTkLabel(self, text=app.t("system_info"),
                     font=("Helvetica", 11, "bold"), text_color=C["muted"]).pack(pady=(14,4))

        info = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=10)
        info.pack(pady=4, padx=24, fill="x")
        pm   = app.pkg_manager or "—"
        term = app.terminal    or "—"
        for icon, label, val in [("📦", app.t("pkg_mgr"), pm), ("🖥", app.t("terminal"), term)]:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(row, text=f"{icon}  {label}:",
                         font=("Helvetica",12), text_color=C["muted"]).pack(side="left")
            ctk.CTkLabel(row, text=val,
                         font=("Helvetica",12,"bold"), text_color=C["text"]).pack(side="left", padx=8)

        self.update_repos_btn = ctk.CTkButton(
            self, text=app.t("update_repos"),
            command=self._update_repos, height=36,
            fg_color=C["surface2"], hover_color=C["border"],
            text_color=C["text"], font=("Helvetica",13), corner_radius=8
        )
        self.update_repos_btn.pack(pady=8, padx=24, fill="x")

        make_divider(self)

        # ── Palet Seçimi ──────────────────────────────────────────────────────
        ctk.CTkLabel(self, text=app.t("palettes"),
                     font=("Helvetica", 11, "bold"), text_color=C["muted"]).pack(pady=(14,4))

        pal_frame = ctk.CTkScrollableFrame(self, height=110, fg_color=C["surface"], corner_radius=10)
        pal_frame.pack(padx=24, fill="x")

        for name, colors in PALETTES.items():
            row = ctk.CTkFrame(pal_frame, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=3)

            # Renk önizleme şeridi
            preview = ctk.CTkFrame(row, width=24, height=24, corner_radius=4,
                                   fg_color=colors["accent"])
            preview.pack(side="left", padx=(4,8))
            preview.pack_propagate(False)

            ctk.CTkLabel(row, text=name,
                         font=("Helvetica",13), text_color=C["text"]).pack(side="left")

            # Seçili mi?
            is_current = (name == app.current_palette_name)
            btn_text = "✓ Seçili" if is_current else "Seç"
            ctk.CTkButton(
                row, text=btn_text, width=90, height=28,
                font=("Helvetica",11),
                fg_color=C["accent_dim"] if not is_current else C["accent"],
                hover_color=C["accent_hover"],
                text_color=C["text"], corner_radius=6,
                command=lambda n=name: self._apply_palette(n)
            ).pack(side="right", padx=4)

            # Dışa aktar butonu
            ctk.CTkButton(
                row, text="↓", width=30, height=28,
                font=("Helvetica",13),
                fg_color=C["surface2"], hover_color=C["border"],
                text_color=C["muted"], corner_radius=6,
                command=lambda n=name, c=colors: self._export(n, c)
            ).pack(side="right", padx=(0,2))

        # İçe aktar
        ctk.CTkButton(
            self, text=app.t("import_pal"),
            command=self._import_palette, height=34,
            fg_color="transparent", hover_color=C["surface2"],
            text_color=C["muted"], border_width=1, border_color=C["border"],
            font=("Helvetica",12), corner_radius=8
        ).pack(pady=(10,2), padx=24, fill="x")

        ctk.CTkLabel(self, text=app.t("restart_note"),
                     font=("Helvetica",10), text_color=C["muted"]).pack(pady=(2,4))

        # Kapat
        ctk.CTkButton(
            self, text=app.t("close"), command=self.destroy, height=36,
            fg_color="transparent", hover_color=C["surface2"],
            text_color=C["muted"], border_width=1, border_color=C["border"],
            font=("Helvetica",12), corner_radius=8
        ).pack(pady=(4,16), padx=24, fill="x")

    def _update_repos(self):
        pm, term = self.app.pkg_manager, self.app.terminal
        if not term: return
        cmds = {"pacman":"sudo pacman -Sy","apt":"sudo apt update",
                "dnf":"sudo dnf check-update","zypper":"sudo zypper refresh"}
        run_in_terminal(term, cmds.get(pm,"echo Unsupported"))

    def _apply_palette(self, name):
        save_theme(name)
        self.app.set_status(f"✓ '{name}' seçildi — uygulamayı yeniden başlat", C["active"])
        self.destroy()

    def _export(self, name, colors):
        path = os.path.join(CONFIG_DIR, f"{name.replace(' ','_')}.json")
        export_palette(name, colors, path)
        self.app.set_status(f"↓ {path}", C["active"])

    def _import_palette(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Palet Seç", filetypes=[("JSON","*.json")], initialdir=CONFIG_DIR
        )
        if not path: return
        try:
            with open(path) as f:
                data = json.load(f)
            name   = data.get("name", os.path.basename(path))
            colors = data.get("colors", data)
            PALETTES[name] = colors
            save_theme(name, colors)
            self.app.set_status(f"✓ '{name}' içe aktarıldı — yeniden başlat", C["active"])
            self.destroy()
        except Exception as e:
            self.app.set_status(f"Hata: {e}", C["red"])

# ── Güncelleme Penceresi ──────────────────────────────────────────────────────

class UpdateWindow(ctk.CTkToplevel):
    def __init__(self, app, results):
        super().__init__(app)
        self.title(app.t("update_title"))
        self.geometry("400x340")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.after(120, self.lift)
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text=app.t("update_title"),
                     font=("Helvetica",18,"bold"), text_color=C["text"]).pack(pady=(24,4))
        make_divider(self)

        scroll = ctk.CTkScrollableFrame(self, height=200, fg_color=C["surface"], corner_radius=10)
        scroll.pack(padx=20, pady=14, fill="x")

        for display, has_update, latest in results:
            row = ctk.CTkFrame(scroll, fg_color=C["surface2"] if has_update else "transparent",
                               corner_radius=8)
            row.pack(fill="x", padx=4, pady=3)

            icon  = "⬆" if has_update else "✓"
            color = C["accent"] if has_update else C["green"]
            ctk.CTkLabel(row, text=f"  {icon}  {display}",
                         font=("Helvetica",13,"bold"), text_color=color).pack(side="left", padx=8, pady=8)
            if has_update:
                ctk.CTkLabel(row, text=f"→ {latest}",
                             font=("Helvetica",11), text_color=C["muted"]).pack(side="left")

            if has_update:
                ctk.CTkButton(
                    row, text="Güncelle" if app.lang=="TR" else "Update",
                    width=90, height=28, font=("Helvetica",11),
                    fg_color=C["accent_dim"], hover_color=C["accent_hover"],
                    text_color=C["text"], corner_radius=6,
                    command=lambda d=display: self._update(app, d)
                ).pack(side="right", padx=8, pady=6)

        ctk.CTkButton(self, text=app.t("close"), command=self.destroy, height=36,
                      fg_color="transparent", hover_color=C["surface2"],
                      text_color=C["muted"], border_width=1, border_color=C["border"],
                      font=("Helvetica",12), corner_radius=8).pack(pady=12, padx=20, fill="x")

    def _update(self, app, display):
        m = re.search(r'(\d+)', display)
        if not m: return
        ver = m.group(1)
        cmd = build_install_cmd(ver, "jdk", app.pkg_manager)
        run_in_terminal(app.terminal, cmd)
        self.destroy()

# ── Ana Uygulama ──────────────────────────────────────────────────────────────

class JavaManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("JavaManager")
        self.geometry("600x660")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.lang                 = "TR"
        self.pkg_manager          = detect_pkg_manager()
        self.terminal             = detect_terminal()
        self.current_palette_name = _theme_name
        self._javas_cache         = []
        self._build_ui()
        self.refresh_list()
        # Açılışta GitHub güncelleme kontrolü (arka planda)
        threading.Thread(target=self._startup_update_check, daemon=True).start()

    def t(self, k): return TEXTS[self.lang][k]

    def set_status(self, msg, color=None):
        self.status_lbl.configure(text=msg, text_color=color or C["muted"])

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):

        # Başlık
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(22,10))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="☕", font=("Helvetica",26)).pack(side="left", padx=(0,8))
        self.title_lbl = ctk.CTkLabel(left, text=self.t("title"),
                                      font=("Helvetica",23,"bold"), text_color=C["text"])
        self.title_lbl.pack(side="left")

        # Sağ üst butonlar
        rbtn = ctk.CTkFrame(header, fg_color="transparent")
        rbtn.pack(side="right")
        self.update_btn = ctk.CTkButton(
            rbtn, text="⬆", width=36, height=36, font=("Helvetica",15),
            fg_color=C["surface2"], hover_color=C["accent_dim"],
            text_color=C["muted"], corner_radius=8,
            command=self._check_updates
        )
        self.update_btn.pack(side="left", padx=(0,6))
        ctk.CTkButton(
            rbtn, text="⚙", width=36, height=36, font=("Helvetica",15),
            fg_color=C["surface2"], hover_color=C["border"],
            text_color=C["muted"], corner_radius=8,
            command=lambda: SettingsWindow(self)
        ).pack(side="left")

        make_divider(self)

        # ── Güncelleme Banner (başlangıçta gizli) ────────────────────────────
        self.update_banner = ctk.CTkFrame(self, fg_color=C["accent_dim"], corner_radius=8)
        # pack edilmez — güncelleme varsa gösterilir

        self._banner_left = ctk.CTkFrame(self.update_banner, fg_color="transparent")
        self._banner_left.pack(side="left", padx=12, pady=8)
        self._banner_icon = ctk.CTkLabel(
            self._banner_left, text="⬆  ",
            font=("Helvetica", 13, "bold"), text_color=C["active"]
        )
        self._banner_icon.pack(side="left")
        self._banner_msg = ctk.CTkLabel(
            self._banner_left, text="",
            font=("Helvetica", 13), text_color=C["text"]
        )
        self._banner_msg.pack(side="left")

        self._banner_dl = ctk.CTkButton(
            self.update_banner, text=self.t("download"),
            width=90, height=28, font=("Helvetica", 12),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="white", corner_radius=6,
            command=self._open_release_page
        )
        self._banner_dl.pack(side="right", padx=8)

        ctk.CTkButton(
            self.update_banner, text="✕", width=28, height=28,
            font=("Helvetica", 12), fg_color="transparent",
            hover_color=C["border"], text_color=C["muted"], corner_radius=6,
            command=self._hide_banner
        ).pack(side="right", padx=(0, 4))

        self._release_url = RELEASES_URL

        # Aktif sürüm şeridi
        strip = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=10)
        strip.pack(fill="x", padx=20, pady=12)

        left_s = ctk.CTkFrame(strip, fg_color="transparent")
        left_s.pack(side="left", padx=14, pady=10)
        self.active_title_lbl = ctk.CTkLabel(
            left_s, text=self.t("active").upper(),
            font=("Helvetica",9,"bold"), text_color=C["muted"]
        )
        self.active_title_lbl.pack(anchor="w")
        self.active_lbl = ctk.CTkLabel(
            left_s, text=self.t("none"),
            font=("Helvetica",15,"bold"), text_color=C["active"]
        )
        self.active_lbl.pack(anchor="w")

        self.refresh_btn = ctk.CTkButton(
            strip, text=self.t("refresh"), width=88, height=30,
            font=("Helvetica",12), fg_color=C["surface2"],
            hover_color=C["border"], text_color=C["text"], corner_radius=6,
            command=self.refresh_list
        )
        self.refresh_btn.pack(side="right", padx=12, pady=10)

        # Liste başlığı
        lbl_row = ctk.CTkFrame(self, fg_color="transparent")
        lbl_row.pack(fill="x", padx=24, pady=(4,4))
        self.list_label = ctk.CTkLabel(
            lbl_row, text=self.t("installed").upper(),
            font=("Helvetica",9,"bold"), text_color=C["muted"]
        )
        self.list_label.pack(side="left")

        # Liste çerçevesi — sabit yükseklik, temiz görünüm
        self.list_frame = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=10)
        self.list_frame.pack(padx=20, fill="x")
        self.list_inner = ctk.CTkScrollableFrame(
            self.list_frame, height=180,
            fg_color="transparent", scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["accent"]
        )
        self.list_inner.pack(fill="x", padx=4, pady=4)

        make_divider(self)

        # Kurulum seçenekleri
        opt = ctk.CTkFrame(self, fg_color="transparent")
        opt.pack(padx=20, pady=10, fill="x")
        opt.columnconfigure(4, weight=1)

        self.ver_label = ctk.CTkLabel(opt, text=self.t("version").upper(),
                                      font=("Helvetica",9,"bold"), text_color=C["muted"])
        self.ver_label.grid(row=0, column=0, padx=(4,8), sticky="w")

        self.version_combo = ctk.CTkComboBox(
            opt, values=["21","17","11","8"], width=80, height=34,
            font=("Helvetica",13),
            fg_color=C["surface2"], border_color=C["border"],
            button_color=C["border"], button_hover_color=C["accent"],
            dropdown_fg_color=C["surface2"], text_color=C["text"],
        )
        self.version_combo.set("21")
        self.version_combo.grid(row=0, column=1, padx=(0,16))

        self.type_var = ctk.StringVar(value="jdk")
        self.radio_btns = []
        for i, (lbl, val) in enumerate([("JDK","jdk"),("JRE","jre")]):
            rb = ctk.CTkRadioButton(
                opt, text=lbl, variable=self.type_var, value=val,
                font=("Helvetica",13), fg_color=C["accent"],
                hover_color=C["accent_dim"], text_color=C["text"]
            )
            rb.grid(row=0, column=2+i, padx=8)
            self.radio_btns.append(rb)

        pm_str = self.pkg_manager or "?"
        self.pm_label = ctk.CTkLabel(opt, text=f"via {pm_str}",
                                     font=("Helvetica",11), text_color=C["muted"])
        self.pm_label.grid(row=0, column=4, sticky="e", padx=(0,4))

        # Kur butonu
        self.install_btn = ctk.CTkButton(
            self, text=self.t("install_btn"),
            command=self.do_install, height=48,
            font=("Helvetica",15,"bold"),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="white", corner_radius=10
        )
        self.install_btn.pack(padx=20, pady=(4,8), fill="x")

        # Durum
        self.status_lbl = ctk.CTkLabel(
            self, text=self.t("ready"),
            font=("Helvetica",11), text_color=C["muted"]
        )
        self.status_lbl.pack(pady=(0,14))

    # ── Uygulama Güncelleme Kontrolü ─────────────────────────────────────────

    def _startup_update_check(self):
        latest, has_update, url = check_github_update()
        if has_update:
            self.after(0, lambda: self._show_banner(latest, url))

    def _show_banner(self, latest, url):
        self._release_url = url
        self._banner_msg.configure(
            text=f"{self.t('app_update')}: {latest}  (şu an {APP_VERSION})"
        )
        self._banner_dl.configure(text=self.t("download"))
        self.update_banner.pack(fill="x", padx=20, pady=(10, 0))

    def _hide_banner(self):
        self.update_banner.pack_forget()

    def _open_release_page(self):
        subprocess.Popen(["xdg-open", self._release_url])

    # ── Liste ─────────────────────────────────────────────────────────────────

    def refresh_list(self):
        self.set_status(self.t("scanning"), C["accent"])
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        javas = scan_javas(self.pkg_manager)
        self._javas_cache = javas
        self.after(0, lambda: self._populate(javas))

    def _populate(self, javas):
        for w in self.list_inner.winfo_children():
            w.destroy()

        if not javas:
            ctk.CTkLabel(self.list_inner, text=self.t("no_java"),
                         font=("Helvetica",13), text_color=C["muted"]).pack(pady=28)
            self.active_lbl.configure(text=self.t("none"))
            self.set_status(self.t("ready"))
            return

        active_display = self.t("none")

        for display, folder, is_def in javas:
            row_bg = C["row_def"] if is_def else "transparent"
            row = ctk.CTkFrame(self.list_inner, fg_color=row_bg, corner_radius=8, height=52)
            row.pack(fill="x", padx=2, pady=2)
            row.pack_propagate(False)

            # Sol çizgi göstergesi
            bar = ctk.CTkFrame(row, width=3, fg_color=C["active"] if is_def else C["border"],
                                corner_radius=2)
            bar.pack(side="left", padx=(8,10), pady=10, fill="y")
            bar.pack_propagate(False)

            # İsim + default etiketi
            name_col = ctk.CTkFrame(row, fg_color="transparent")
            name_col.pack(side="left", pady=0)
            ctk.CTkLabel(name_col, text=display,
                         font=("Helvetica",13,"bold"), text_color=C["text"],
                         anchor="w").pack(anchor="w")
            if is_def:
                ctk.CTkLabel(name_col, text="default",
                             font=("Helvetica",9), text_color=C["active"],
                             anchor="w").pack(anchor="w")
                active_display = display

            # Butonlar
            btn_grp = ctk.CTkFrame(row, fg_color="transparent")
            btn_grp.pack(side="right", padx=8)

            ctk.CTkButton(
                btn_grp, text=self.t("set_def"), width=100, height=28,
                font=("Helvetica",11),
                fg_color=C["green_dim"] if is_def else C["accent_dim"],
                hover_color=C["green"] if is_def else C["accent_hover"],
                text_color=C["text"], corner_radius=6,
                command=lambda f=folder: self._set_default(f)
            ).pack(side="left", padx=3)

            ctk.CTkButton(
                btn_grp, text=self.t("remove"), width=76, height=28,
                font=("Helvetica",11),
                fg_color="transparent", hover_color=C["red_dim"],
                text_color=C["muted"], corner_radius=6,
                border_width=1, border_color=C["border"],
                command=lambda f=folder: self._remove(f)
            ).pack(side="left", padx=3)

        self.active_lbl.configure(text=active_display)
        self.set_status(self.t("ready"))

    # ── Güncelleme Kontrolü ───────────────────────────────────────────────────

    def _check_updates(self):
        if not self._javas_cache:
            self.set_status(self.t("scanning"), C["accent"])
            self.refresh_list()
            return
        self.set_status(self.t("checking"), C["accent"])
        self.update_btn.configure(state="disabled")

        def _worker():
            results = check_updates_for(self._javas_cache, self.pkg_manager)
            self.after(0, lambda: self._show_update_results(results))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_update_results(self, results):
        self.update_btn.configure(state="normal")
        any_update = any(r[1] for r in results)
        self.set_status(
            self.t("update_avail") if any_update else self.t("up_to_date"),
            C["accent"] if any_update else C["green"]
        )
        UpdateWindow(self, results)

    # ── Eylemler ──────────────────────────────────────────────────────────────

    def _set_default(self, folder):
        if not self.terminal:
            self.set_status(self.t("no_term"), C["red"]); return
        cmd = build_set_default_cmd(folder, self.pkg_manager)
        if not cmd:
            self.set_status(self.t("no_pm"), C["red"]); return
        self.set_status(self.t("setting"), C["accent"])
        run_in_terminal(self.terminal, cmd)
        threading.Timer(6.0, lambda: self.after(0, self.refresh_list)).start()

    def _remove(self, folder):
        if not self.terminal:
            self.set_status(self.t("no_term"), C["red"]); return
        cmd = build_remove_cmd(folder, self.pkg_manager)
        if not cmd: return
        self.set_status(self.t("removing"), C["red"])
        run_in_terminal(self.terminal, cmd)
        threading.Timer(10.0, lambda: self.after(0, self.refresh_list)).start()

    def do_install(self):
        if not self.pkg_manager:
            self.set_status(self.t("no_pm"), C["red"]); return
        if not self.terminal:
            self.set_status(self.t("no_term"), C["red"]); return
        cmd = build_install_cmd(self.version_combo.get(), self.type_var.get(), self.pkg_manager)
        if not cmd: return
        self.set_status(self.t("installing"), C["accent"])
        run_in_terminal(self.terminal, cmd)
        threading.Timer(18.0, lambda: self.after(0, self.refresh_list)).start()

    # ── Dil ───────────────────────────────────────────────────────────────────

    def change_lang(self, choice):
        self.lang = choice
        self.title_lbl.configure(text=self.t("title"))
        self.active_title_lbl.configure(text=self.t("active").upper())
        self.list_label.configure(text=self.t("installed").upper())
        self.install_btn.configure(text=self.t("install_btn"))
        self.refresh_btn.configure(text=self.t("refresh"))
        self.ver_label.configure(text=self.t("version").upper())
        self.status_lbl.configure(text=self.t("ready"))
        self.refresh_list()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = JavaManager()
    app.mainloop()
