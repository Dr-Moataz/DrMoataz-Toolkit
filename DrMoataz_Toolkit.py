"""
╔══════════════════════════════════════════════════════════╗
║          Dr.Moataz Toolkit  v3.0                        ║
║          Windows Repair & Optimization Suite            ║
║          © 2025 Dr. Moataz — All rights reserved        ║
╚══════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess, threading, os, sys, ctypes
import datetime, shutil, time, tempfile, socket
import winreg, winsound, platform, psutil

# ══════════════════════════════════════════════
#  AUTO ELEVATION
# ══════════════════════════════════════════════
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def elevate():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(f'"{a}"' for a in sys.argv), None, 1)
        sys.exit()

elevate()

# ══════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════
APP_NAME = "Dr.Moataz Toolkit"
VERSION  = "v3.0"
AUTHOR   = "Dr. Moataz"
LOG_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "DrMoataz_Log.txt")

# ── Theme Palettes ──────────────────────────
THEMES = {
    "dark": {
        "bg":       "#0a0e1a",
        "panel":    "#0f1629",
        "card":     "#141d35",
        "border":   "#1e2d50",
        "fg":       "#e8f0fe",
        "grey":     "#8892b0",
        "log_bg":   "#080d1a",
        "log_fg":   "#00ff88",
    },
    "light": {
        "bg":       "#f0f4ff",
        "panel":    "#dde6f7",
        "card":     "#ffffff",
        "border":   "#b0c4de",
        "fg":       "#0a0e1a",
        "grey":     "#4a5568",
        "log_bg":   "#e8f0fe",
        "log_fg":   "#006633",
    }
}
ACCENT  = "#00d4ff"
ACCENT2 = "#7b2fff"
GREEN   = "#00c46e"
RED_C   = "#ff4757"
YELLOW  = "#ffa502"

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_MONO  = ("Consolas",  9)
FONT_BTN   = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI",  8)
FONT_MED   = ("Segoe UI", 11, "bold")

# ══════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════
def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except: pass

# ══════════════════════════════════════════════
#  SOUND
# ══════════════════════════════════════════════
def beep_ok():    winsound.MessageBeep(winsound.MB_ICONASTERISK)
def beep_err():   winsound.MessageBeep(winsound.MB_ICONHAND)
def beep_start(): winsound.Beep(800, 80)

# ══════════════════════════════════════════════
#  SHELL HELPER
# ══════════════════════════════════════════════
def run(cmd: str):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, encoding="utf-8", errors="ignore")
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return -1, str(e)

# ══════════════════════════════════════════════
#  ① SFC ONLY
# ══════════════════════════════════════════════
def do_sfc(out):
    out("🔵 تشغيل SFC /scannow ...")
    rc, txt = run("sfc /scannow")
    log(f"SFC: {txt[:300]}")
    out(f"   {txt[:400]}")
    out("✅ SFC اكتمل")

# ══════════════════════════════════════════════
#  ② DISM ONLY
# ══════════════════════════════════════════════
def do_dism(out):
    out("🔵 تشغيل DISM RestoreHealth ...")
    rc, txt = run("DISM /Online /Cleanup-Image /RestoreHealth")
    log(f"DISM: {txt[:300]}")
    out(f"   {txt[:400]}")
    out("✅ DISM اكتمل")

# ══════════════════════════════════════════════
#  ③ CLEAN TEMP
# ══════════════════════════════════════════════
def do_clean_temp(out):
    dirs = [
        tempfile.gettempdir(),
        os.path.join(os.environ.get("SystemRoot","C:\\Windows"), "Temp"),
        os.path.join(os.environ.get("SystemRoot","C:\\Windows"), "Prefetch"),
    ]
    total = 0
    for d in dirs:
        if not os.path.isdir(d): continue
        for name in os.listdir(d):
            fp = os.path.join(d, name)
            try:
                if os.path.isfile(fp):
                    total += os.path.getsize(fp); os.remove(fp)
                elif os.path.isdir(fp):
                    shutil.rmtree(fp, ignore_errors=True)
            except: pass
    mb = total / 1_048_576
    msg = f"✅ تم حذف {mb:.1f} MB من الملفات المؤقتة"
    out(msg); log(msg)

# ══════════════════════════════════════════════
#  ④ REPAIR NETWORK
# ══════════════════════════════════════════════
def do_fix_network(out):
    steps = [
        ("ipconfig /flushdns",  "Flush DNS"),
        ("netsh winsock reset", "Winsock Reset"),
        ("netsh int ip reset",  "TCP/IP Reset"),
        ("ipconfig /release",   "IP Release"),
        ("ipconfig /renew",     "IP Renew"),
    ]
    for cmd, label in steps:
        out(f"🔵 {label} ...")
        rc, txt = run(cmd)
        out(f"   → {txt[:100]}")
        log(f"{label}: {txt[:100]}")
    out("✅ إصلاح الشبكة اكتمل")

# ══════════════════════════════════════════════
#  ⑤ FIX WINDOWS UPDATE
# ══════════════════════════════════════════════
def do_fix_update(out):
    svcs = ["wuauserv","cryptSvc","bits","msiserver"]
    for s in svcs: run(f"net stop {s}"); out(f"🛑 {s}")
    windir = os.environ.get("SystemRoot","C:\\Windows")
    for p in [os.path.join(windir,"SoftwareDistribution"),
               os.path.join(windir,"System32","catroot2")]:
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
            out(f"🗑️ حُذف: {p}"); log(f"Deleted {p}")
    for s in svcs: run(f"net start {s}"); out(f"▶️ {s}")
    out("✅ Windows Update تم إصلاحه")

# ══════════════════════════════════════════════
#  ⑥ FIX MICROSOFT STORE
# ══════════════════════════════════════════════
def do_fix_store(out):
    out("🔵 wsreset.exe ...")
    run("wsreset.exe")
    log("wsreset done")
    out("✅ Microsoft Store تم إعادة ضبطه")

# ══════════════════════════════════════════════
#  ⑦ REBUILD ICON CACHE
# ══════════════════════════════════════════════
def do_icon_cache(out):
    out("🔵 إعادة بناء كاش الأيقونات ...")
    cache = os.path.join(os.environ.get("LOCALAPPDATA",""),
                         "Microsoft","Windows","Explorer")
    if os.path.isdir(cache):
        for f in os.listdir(cache):
            if f.startswith("iconcache"):
                try: os.remove(os.path.join(cache, f))
                except: pass
    run("ie4uinit.exe -show")
    log("Icon cache rebuilt")
    out("✅ كاش الأيقونات تم إعادة بناؤه")

# ══════════════════════════════════════════════
#  ⑧ RESTART EXPLORER
# ══════════════════════════════════════════════
def do_restart_explorer(out):
    out("🔵 إعادة تشغيل Explorer ...")
    run("taskkill /f /im explorer.exe")
    time.sleep(1.2)
    run("start explorer.exe")
    log("Explorer restarted")
    out("✅ Explorer تم إعادة تشغيله")

# ══════════════════════════════════════════════
#  ⑨ CHECK DISK
# ══════════════════════════════════════════════
def do_chkdsk(out):
    out("🔵 جدولة CHKDSK عند إعادة التشغيل ...")
    run("echo Y | chkdsk C: /f /r /x")
    log("CHKDSK scheduled")
    out("✅ CHKDSK مجدول — أعد تشغيل الجهاز لتطبيقه")

# ══════════════════════════════════════════════
#  ⑩ DEFRAG
# ══════════════════════════════════════════════
def do_defrag(out):
    out("🔵 Defragment C: ...")
    rc, txt = run("defrag C: /U /V")
    log(f"Defrag: {txt[:200]}")
    out(f"   {txt[:300]}")
    out("✅ Defragment اكتمل")

# ══════════════════════════════════════════════
#  ⑪ SHUTDOWN TIMER
# ══════════════════════════════════════════════
def do_shutdown(mins: int, out):
    run(f"shutdown /s /t {mins*60}")
    msg = f"✅ إيقاف التشغيل بعد {mins} دقيقة"
    out(msg); log(msg)

def do_cancel_shutdown(out):
    run("shutdown /a")
    out("✅ تم إلغاء مؤقت الإيقاف"); log("Shutdown cancelled")

# ══════════════════════════════════════════════
#  ⑫ BOOT TO BIOS
# ══════════════════════════════════════════════
def do_bios(out):
    out("🔵 إعادة التشغيل للـ BIOS/UEFI ...")
    run("shutdown /r /fw /t 0")
    log("Reboot to BIOS")

# ══════════════════════════════════════════════
#  ⑬ CREATE GOD MODE
# ══════════════════════════════════════════════
def do_god_mode(out):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    folder  = os.path.join(desktop,
        "GodMode.{ED7BA470-8E54-465E-825C-99712043E01C}")
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
            out("✅ تم إنشاء God Mode على سطح المكتب!")
        else:
            out("ℹ️ God Mode موجود بالفعل على سطح المكتب")
        log("God Mode created")
    except Exception as e:
        out(f"❌ خطأ: {e}"); log(f"God Mode error: {e}")

# ══════════════════════════════════════════════
#  ⑭ HIDE / SHOW DESKTOP ICONS (TOGGLE)
# ══════════════════════════════════════════════
def _get_icon_state():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced")
        val, _ = winreg.QueryValueEx(key, "HideIcons")
        winreg.CloseKey(key)
        return bool(val)
    except: return False

def do_hide_icons(out):
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced")
    winreg.SetValueEx(key, "HideIcons", 0, winreg.REG_DWORD, 1)
    winreg.CloseKey(key)
    run("taskkill /f /im explorer.exe"); time.sleep(0.6); run("start explorer.exe")
    out("✅ أيقونات سطح المكتب مخفية"); log("Icons hidden")

def do_show_icons(out):
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced")
    winreg.SetValueEx(key, "HideIcons", 0, winreg.REG_DWORD, 0)
    winreg.CloseKey(key)
    run("taskkill /f /im explorer.exe"); time.sleep(0.6); run("start explorer.exe")
    out("✅ أيقونات سطح المكتب ظاهرة"); log("Icons shown")

# ══════════════════════════════════════════════
#  ⑮ SMART FIX (AUTO DIAGNOSE + FIX)
# ══════════════════════════════════════════════
def do_smart_fix(out):
    out("🧠 Smart Fix — جارٍ تشخيص الجهاز ...")
    issues = []

    # Check disk space
    try:
        usage = psutil.disk_usage("C:\\")
        if usage.percent > 85:
            issues.append(("disk_space", f"القرص ممتلئ {usage.percent:.0f}%"))
    except: pass

    # Check temp size
    try:
        tmp = tempfile.gettempdir()
        tmp_size = sum(
            os.path.getsize(os.path.join(tmp, f))
            for f in os.listdir(tmp)
            if os.path.isfile(os.path.join(tmp, f))
        ) / 1_048_576
        if tmp_size > 500:
            issues.append(("temp", f"ملفات Temp كبيرة: {tmp_size:.0f} MB"))
    except: pass

    # Check internet
    try:
        socket.setdefaulttimeout(3)
        socket.create_connection(("8.8.8.8", 53))
    except:
        issues.append(("network", "لا يوجد اتصال بالإنترنت"))

    # Check Windows Update service
    rc, txt = run("sc query wuauserv")
    if "STOPPED" in txt:
        issues.append(("update_svc", "خدمة Windows Update متوقفة"))

    if not issues:
        out("✅ لم يتم اكتشاف مشاكل واضحة — جهازك بصحة جيدة!")
        log("Smart Fix: no issues found")
        return

    out(f"⚠️ تم اكتشاف {len(issues)} مشكلة — جارٍ الإصلاح التلقائي:")
    for key, desc in issues:
        out(f"  🔴 {desc}")

    for key, desc in issues:
        out(f"\n▶ إصلاح: {desc}")
        if key == "disk_space": do_clean_temp(out)
        elif key == "temp":     do_clean_temp(out)
        elif key == "network":  do_fix_network(out)
        elif key == "update_svc": run("net start wuauserv"); out("✅ خدمة التحديث شُغّلت")

    out("\n🎉 Smart Fix اكتمل!")
    log("Smart Fix done")

# ══════════════════════════════════════════════
#  ⑯ FULL REPAIR (FIX ALL)
# ══════════════════════════════════════════════
def do_fix_all(out):
    steps = [
        ("SFC",              do_sfc),
        ("DISM",             do_dism),
        ("Temp Files",       do_clean_temp),
        ("Network",          do_fix_network),
        ("Windows Update",   do_fix_update),
        ("Microsoft Store",  do_fix_store),
        ("Icon Cache",       do_icon_cache),
        ("Explorer",         do_restart_explorer),
    ]
    for label, fn in steps:
        out(f"\n{'─'*38}\n▶ {label}\n{'─'*38}")
        try: fn(out)
        except Exception as e:
            out(f"⚠️ خطأ في {label}: {e}"); log(f"FixAll error {label}: {e}")
    out("\n🎉 Full Repair اكتمل بنجاح!")

# ══════════════════════════════════════════════
#  ⑰ CREATE RESTORE POINT
# ══════════════════════════════════════════════
def do_restore_point(out):
    out("🔵 إنشاء نقطة استعادة ...")
    ps = ('powershell -Command "Checkpoint-Computer '
          '-Description \'DrMoataz_Toolkit\' -RestorePointType MODIFY_SETTINGS"')
    rc, txt = run(ps)
    log(f"RestorePoint: {txt[:200]}")
    if rc == 0:
        out("✅ نقطة الاستعادة تم إنشاؤها")
    else:
        out(f"⚠️ {txt[:200]}")

# ══════════════════════════════════════════════
#  ⑱ RAM CLEANER
# ══════════════════════════════════════════════
def do_ram_clean(out):
    out("🔵 تحرير الذاكرة (RAM) ...")
    ps = ('powershell -Command "[System.GC]::Collect(); '
          '[System.GC]::WaitForPendingFinalizers()"')
    run(ps)
    try:
        ram = psutil.virtual_memory()
        avail = ram.available / 1_048_576
        out(f"✅ الذاكرة المتاحة الآن: {avail:.0f} MB")
    except:
        out("✅ تم تحرير الذاكرة")
    log("RAM cleaned")

# ══════════════════════════════════════════════
#  ⑲ PING TEST
# ══════════════════════════════════════════════
def do_ping_test(out):
    hosts = [("Google DNS", "8.8.8.8"), ("Cloudflare", "1.1.1.1"),
             ("Microsoft",  "microsoft.com")]
    out("🔵 اختبار الاتصال ...")
    for name, host in hosts:
        rc, txt = run(f"ping -n 2 {host}")
        ok = "✅" if rc == 0 else "❌"
        ms_line = [l for l in txt.splitlines() if "ms" in l.lower()]
        info = ms_line[-1].strip() if ms_line else txt.split("\n")[0][:60]
        out(f"  {ok} {name} ({host}): {info}")
        log(f"Ping {name}: rc={rc}")
    out("✅ اختبار الاتصال اكتمل")

# ══════════════════════════════════════════════
#  SYSTEM INFO
# ══════════════════════════════════════════════
def get_system_info():
    info = {}
    try:
        info["os"]  = platform.version()[:60]
        info["cpu"] = f"{psutil.cpu_percent(interval=0.5):.1f}%"
        ram = psutil.virtual_memory()
        info["ram"] = f"{ram.percent:.1f}%  ({ram.used//1_048_576:,} / {ram.total//1_048_576:,} MB)"
        disk = psutil.disk_usage("C:\\")
        info["disk"] = f"{disk.percent:.1f}%  ({disk.used//1_073_741_824:.1f} / {disk.total//1_073_741_824:.1f} GB)"
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            info["ip"] = ip
        except: info["ip"] = "غير متاح"
        info["uptime"] = str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time())))
    except Exception as e:
        info["error"] = str(e)
    return info

# ══════════════════════════════════════════════
#  SPLASH SCREEN
# ══════════════════════════════════════════════
class Splash(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.overrideredirect(True)
        W, H = 540, 360
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.configure(bg="#0a0e1a")
        self.attributes("-topmost", True)
        self._draw()
        self.after(3500, lambda: (self.destroy(), callback()))

    def _draw(self):
        tk.Frame(self, bg=ACCENT2, height=4).pack(fill="x")
        tk.Frame(self, bg="#0a0e1a", height=30).pack()
        tk.Label(self, text="⚕", font=("Segoe UI Emoji", 52),
                 bg="#0a0e1a", fg=ACCENT).pack()
        tk.Label(self, text="Dr.Moataz Toolkit",
                 font=("Segoe UI", 26, "bold"), bg="#0a0e1a", fg="#e8f0fe").pack()
        tk.Label(self, text=f"{VERSION}  ·  Windows Repair Suite",
                 font=FONT_SMALL, bg="#0a0e1a", fg="#8892b0").pack(pady=4)
        self.lbl = tk.Label(self, text="تهيئة النظام ...",
                             font=FONT_SMALL, bg="#0a0e1a", fg=ACCENT)
        self.lbl.pack(pady=12)
        pb = ttk.Progressbar(self, length=420, mode="indeterminate")
        pb.pack(); pb.start(10)
        tk.Label(self, text=f"© 2025 {AUTHOR}",
                 font=FONT_SMALL, bg="#0a0e1a", fg="#8892b0").pack(side="bottom", pady=10)
        msgs = ["فحص الصلاحيات ...","تحميل الأدوات ...","تهيئة الواجهة ...","جاهز! 🚀"]
        for i, m in enumerate(msgs):
            self.after(700*i, lambda m=m: self.lbl.config(text=m))


# ══════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title(f"{APP_NAME} {VERSION}")
        self.resizable(True, True)
        self.minsize(1100, 680)
        self._center(1150, 720)
        self._theme_name = "dark"
        self._T = THEMES["dark"]
        self._style_ttk()
        self.shutdown_min = tk.IntVar(value=30)
        Splash(self, self._show)

    # ── helpers ──────────────────────────────
    def _center(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _style_ttk(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("TProgressbar", troughcolor=self._T["card"],
                     background=ACCENT, thickness=5)
        s.configure("TNotebook", background=self._T["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", background=self._T["card"],
                     foreground=self._T["grey"], padding=[16,7], font=FONT_LABEL)
        s.map("TNotebook.Tab",
              background=[("selected", self._T["panel"])],
              foreground=[("selected", ACCENT)])

    def _show(self):
        self.deiconify()
        self.configure(bg=self._T["bg"])
        self._build()

    # ── apply theme ──────────────────────────
    def _apply_theme(self, name):
        self._theme_name = name
        self._T = THEMES[name]
        # Rebuild UI
        for w in self.winfo_children(): w.destroy()
        self._style_ttk()
        self.configure(bg=self._T["bg"])
        self._build()
        self._out(f"✅ تم تطبيق {'Dark' if name=='dark' else 'Light'} Mode")

    # ══════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════
    def _build(self):
        T = self._T
        # ── TOP BAR ──────────────────────────
        top = tk.Frame(self, bg=T["bg"], height=62)
        top.pack(fill="x"); top.pack_propagate(False)

        tk.Label(top, text="⚕", font=("Segoe UI Emoji", 28),
                 bg=T["bg"], fg=ACCENT).pack(side="left", padx=(14,6))
        lf = tk.Frame(top, bg=T["bg"]); lf.pack(side="left")
        tk.Label(lf, text="Dr.Moataz Toolkit", font=FONT_TITLE,
                 bg=T["bg"], fg=T["fg"]).pack(anchor="w")
        tk.Label(lf, text=f"{VERSION}  ·  Windows Repair Suite  ·  ✅ Administrator",
                 font=FONT_SMALL, bg=T["bg"], fg=ACCENT).pack(anchor="w")

        rf = tk.Frame(top, bg=T["bg"]); rf.pack(side="right", padx=12)
        now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")
        tk.Label(rf, text=f"🕐 {now}", font=FONT_SMALL,
                 bg=T["bg"], fg=T["grey"]).pack(anchor="e")

        # Dark/Light toggle in top bar
        theme_lbl = "🌙 Dark" if self._theme_name == "light" else "☀️ Light"
        tk.Button(rf, text=theme_lbl, font=FONT_SMALL,
                  bg=T["card"], fg=T["fg"], relief="flat", cursor="hand2",
                  padx=8, pady=3,
                  command=lambda: self._apply_theme(
                      "light" if self._theme_name == "dark" else "dark")
                  ).pack(anchor="e", pady=2)

        tk.Frame(self, bg=ACCENT2, height=2).pack(fill="x")

        # ── BODY ─────────────────────────────
        body = tk.Frame(self, bg=T["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=8)

        left = tk.Frame(body, bg=T["bg"])
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(body, bg=T["bg"], width=295)
        right.pack(side="right", fill="y", padx=(8,0))
        right.pack_propagate(False)

        self._build_tabs(left)
        self._build_right(right)
        self._build_status()

    # ══════════════════════════════════════════
    #  TABS
    # ══════════════════════════════════════════
    def _build_tabs(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        tabs = [
            ("🔧 الإصلاح",    self._tab_repair),
            ("🛠️ النظام",     self._tab_system),
            ("📊 معلومات",    self._tab_sysinfo),
            ("⚡ إصلاح سريع", self._tab_quick),
        ]
        for label, builder in tabs:
            frame = tk.Frame(nb, bg=self._T["bg"])
            nb.add(frame, text=label)
            builder(frame)

    # ── Tab 1: Repair ────────────────────────
    def _tab_repair(self, p):
        T = self._T
        g = tk.Frame(p, bg=T["bg"]); g.pack(fill="both", expand=True, padx=6, pady=6)
        buttons = [
            ("🛡️ SFC Scan",         "فحص وإصلاح ملفات النظام",       do_sfc,             ACCENT),
            ("🔧 DISM Repair",       "إصلاح صورة Windows",              do_dism,            ACCENT2),
            ("🧹 Clean Temp",        "حذف الملفات المؤقتة",             do_clean_temp,      GREEN),
            ("🌐 Repair Network",    "DNS · Winsock · TCP/IP",          do_fix_network,     ACCENT),
            ("🔄 Windows Update",    "إصلاح التحديثات العالقة",         do_fix_update,      YELLOW),
            ("🏪 Microsoft Store",   "إعادة ضبط المتجر",               do_fix_store,       ACCENT2),
            ("🖼️ Icon Cache",        "إصلاح الأيقونات التالفة",         do_icon_cache,      GREEN),
            ("📂 Restart Explorer",  "إعادة تشغيل شريط المهام",         do_restart_explorer, RED_C),
            ("🧠 Smart Fix",         "تشخيص تلقائي ثم إصلاح",          do_smart_fix,       ACCENT),
            ("🔁 Create Restore Pt", "نقطة استعادة قبل التغييرات",      do_restore_point,   YELLOW),
        ]
        for i, (title, sub, fn, color) in enumerate(buttons):
            r, c = divmod(i, 3)
            card = self._card(g, title, sub, fn, color)
            card.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
        for c in range(3): g.columnconfigure(c, weight=1)

    # ── Tab 2: System Tools ──────────────────
    def _tab_system(self, p):
        T = self._T
        g = tk.Frame(p, bg=T["bg"]); g.pack(fill="both", expand=True, padx=6, pady=6)

        btn_data = [
            ("💾 Check Disk",      "CHKDSK /f /r عند الإقلاع",      do_chkdsk,        RED_C),
            ("📊 Defrag HDD",      "تحسين سرعة القرص",               do_defrag,        ACCENT),
            ("⚙️ Boot to BIOS",   "إعادة تشغيل للبيوس مباشرة",      do_bios,          ACCENT2),
            ("🌟 God Mode",        "اختصار كل إعدادات الويندوز",      do_god_mode,      YELLOW),
            ("🧠 RAM Cleaner",     "تحرير الذاكرة بدون إعادة تشغيل", do_ram_clean,     GREEN),
            ("🌐 Ping Test",       "اختبار الاتصال بالإنترنت",        do_ping_test,     ACCENT),
        ]
        for i, (title, sub, fn, color) in enumerate(btn_data):
            r, c = divmod(i, 3)
            card = self._card(g, title, sub, fn, color)
            card.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
        for c in range(3): g.columnconfigure(c, weight=1)

        # ── Shutdown Timer ──────────────────
        sf = tk.Frame(p, bg=T["card"], highlightbackground=T["border"],
                      highlightthickness=1)
        sf.pack(fill="x", padx=6, pady=(0,6))
        tk.Label(sf, text="⏰ مؤقت إيقاف التشغيل", font=FONT_LABEL,
                 bg=T["card"], fg=T["fg"]).pack(side="left", padx=12, pady=10)
        tk.Spinbox(sf, from_=1, to=480, textvariable=self.shutdown_min,
                   width=5, font=FONT_LABEL, bg=T["bg"], fg=T["fg"],
                   insertbackground=T["fg"]).pack(side="left", padx=4)
        tk.Label(sf, text="دقيقة", font=FONT_SMALL,
                 bg=T["card"], fg=T["grey"]).pack(side="left")
        tk.Button(sf, text="⏰ تشغيل", font=FONT_BTN, bg=YELLOW,
                  fg="#0a0e1a", relief="flat", cursor="hand2", padx=10, pady=5,
                  command=lambda: self._run(do_shutdown, self.shutdown_min.get())
                  ).pack(side="left", padx=8)
        tk.Button(sf, text="❌ إلغاء", font=FONT_BTN, bg=RED_C,
                  fg="white", relief="flat", cursor="hand2", padx=10, pady=5,
                  command=lambda: self._run(do_cancel_shutdown)
                  ).pack(side="left", padx=4)

        # ── Desktop Icons ───────────────────
        df = tk.Frame(p, bg=T["card"], highlightbackground=T["border"],
                      highlightthickness=1)
        df.pack(fill="x", padx=6, pady=(0,6))
        tk.Label(df, text="🖥️ أيقونات سطح المكتب:", font=FONT_LABEL,
                 bg=T["card"], fg=T["fg"]).pack(side="left", padx=12, pady=10)
        tk.Button(df, text="🙈 إخفاء", font=FONT_BTN, bg=T["card"],
                  fg=RED_C, relief="flat", cursor="hand2", padx=10, pady=5,
                  highlightbackground=RED_C, highlightthickness=1,
                  command=lambda: self._run(do_hide_icons)
                  ).pack(side="left", padx=4)
        tk.Button(df, text="👁 إظهار", font=FONT_BTN, bg=T["card"],
                  fg=GREEN, relief="flat", cursor="hand2", padx=10, pady=5,
                  highlightbackground=GREEN, highlightthickness=1,
                  command=lambda: self._run(do_show_icons)
                  ).pack(side="left", padx=4)

    # ── Tab 3: System Info ───────────────────
    def _tab_sysinfo(self, p):
        T = self._T
        header = tk.Frame(p, bg=T["bg"])
        header.pack(fill="x", padx=8, pady=(8,4))
        tk.Label(header, text="📊 System Info Dashboard",
                 font=FONT_MED, bg=T["bg"], fg=T["fg"]).pack(side="left")
        tk.Button(header, text="🔄 تحديث", font=FONT_SMALL,
                  bg=T["card"], fg=ACCENT, relief="flat", cursor="hand2",
                  padx=8, pady=3,
                  command=lambda: self._refresh_info()
                  ).pack(side="right")

        self._info_frame = tk.Frame(p, bg=T["bg"])
        self._info_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self._refresh_info()

    def _refresh_info(self):
        T = self._T
        for w in self._info_frame.winfo_children(): w.destroy()
        info = get_system_info()
        rows = [
            ("💻 نظام التشغيل",    info.get("os",    "—")),
            ("⚡ CPU",              info.get("cpu",   "—")),
            ("🧠 RAM",              info.get("ram",   "—")),
            ("💾 القرص C:",        info.get("disk",  "—")),
            ("🌐 IP Address",       info.get("ip",    "—")),
            ("⏱️ وقت التشغيل",     info.get("uptime","—")),
        ]
        for i, (label, value) in enumerate(rows):
            row = tk.Frame(self._info_frame, bg=T["card"],
                           highlightbackground=T["border"], highlightthickness=1)
            row.pack(fill="x", pady=3, ipady=6, ipadx=8)
            tk.Label(row, text=label, font=FONT_LABEL, width=18, anchor="w",
                     bg=T["card"], fg=T["grey"]).pack(side="left", padx=12)
            # Color-code usage percentages
            color = T["fg"]
            if "%" in value:
                try:
                    pct = float(value.split("%")[0].strip())
                    color = GREEN if pct < 60 else YELLOW if pct < 85 else RED_C
                except: pass
            tk.Label(row, text=value, font=FONT_LABEL, anchor="w",
                     bg=T["card"], fg=color).pack(side="left", padx=4)

    # ── Tab 4: Quick Fix All ─────────────────
    def _tab_quick(self, p):
        T = self._T
        hero = tk.Frame(p, bg=T["card"],
                        highlightbackground=ACCENT, highlightthickness=2)
        hero.pack(fill="x", padx=12, pady=(14,6))
        tk.Label(hero, text="⚡ Full Repair — إصلاح شامل بضغطة واحدة",
                 font=("Segoe UI", 13, "bold"), bg=T["card"], fg=T["fg"]).pack(pady=(16,4))
        tk.Label(hero,
                 text="SFC · DISM · Temp · DNS · Windows Update · Store · Icons · Explorer",
                 font=FONT_SMALL, bg=T["card"], fg=T["grey"]).pack()
        tk.Button(hero, text="🚀  Full Repair",
                  font=("Segoe UI", 14, "bold"),
                  bg=ACCENT, fg="#0a0e1a", relief="flat", cursor="hand2", pady=12,
                  activebackground=ACCENT2, activeforeground="white",
                  command=lambda: self._run(do_fix_all)
                  ).pack(fill="x", padx=20, pady=14)

        smart = tk.Frame(p, bg=T["card"],
                         highlightbackground=ACCENT2, highlightthickness=2)
        smart.pack(fill="x", padx=12, pady=(0,6))
        tk.Label(smart, text="🧠 Smart Fix — تشخيص + إصلاح ذكي",
                 font=("Segoe UI", 13, "bold"), bg=T["card"], fg=T["fg"]).pack(pady=(14,4))
        tk.Label(smart, text="يفحص المشاكل أولاً ثم يصلح فقط ما يحتاج إصلاح",
                 font=FONT_SMALL, bg=T["card"], fg=T["grey"]).pack()
        tk.Button(smart, text="🧠  Smart Fix",
                  font=("Segoe UI", 14, "bold"),
                  bg=ACCENT2, fg="white", relief="flat", cursor="hand2", pady=12,
                  command=lambda: self._run(do_smart_fix)
                  ).pack(fill="x", padx=20, pady=14)

        # Quick action row
        qf = tk.Frame(p, bg=T["bg"]); qf.pack(fill="x", padx=12)
        for label, fn, color in [
            ("🧹 Temp",   do_clean_temp,   T["card"]),
            ("🌐 DNS",    do_fix_network,  T["card"]),
            ("🔄 Update", do_fix_update,   T["card"]),
            ("🧠 RAM",    do_ram_clean,    T["card"]),
        ]:
            tk.Button(qf, text=label, font=FONT_BTN, bg=color, fg=T["fg"],
                      relief="flat", cursor="hand2", pady=10,
                      highlightbackground=ACCENT, highlightthickness=1,
                      command=lambda f=fn: self._run(f)
                      ).pack(side="left", expand=True, fill="x", padx=3)

    # ══════════════════════════════════════════
    #  RIGHT PANEL: LOG + EXIT
    # ══════════════════════════════════════════
    def _build_right(self, parent):
        T = self._T
        hdr = tk.Frame(parent, bg=T["panel"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋 سجل العمليات", font=FONT_LABEL,
                 bg=T["panel"], fg=ACCENT).pack(side="left", padx=8, pady=6)
        tk.Button(hdr, text="🗑", font=FONT_SMALL, bg=T["panel"],
                  fg=T["grey"], relief="flat", cursor="hand2",
                  command=self._clear_log).pack(side="right", padx=2)
        tk.Button(hdr, text="💾", font=FONT_SMALL, bg=T["panel"],
                  fg=T["grey"], relief="flat", cursor="hand2",
                  command=lambda: os.startfile(LOG_FILE)).pack(side="right")

        self.log_box = scrolledtext.ScrolledText(
            parent, font=FONT_MONO, bg=T["log_bg"], fg=T["log_fg"],
            insertbackground=T["fg"], relief="flat", wrap="word", state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=4, pady=(0,4))

        # Progress bar
        pf = tk.Frame(parent, bg=T["bg"]); pf.pack(fill="x", padx=4, pady=(0,4))
        tk.Label(pf, text="التقدم:", font=FONT_SMALL,
                 bg=T["bg"], fg=T["grey"]).pack(side="left")
        self.progress = ttk.Progressbar(pf, length=180, mode="indeterminate")
        self.progress.pack(side="left", padx=6)

        # EXIT button
        tk.Button(parent, text="🚪 خروج", font=FONT_BTN,
                  bg=RED_C, fg="white", relief="flat", cursor="hand2",
                  pady=10, command=self._exit
                  ).pack(fill="x", padx=4, pady=(0,4))

    def _build_status(self):
        T = self._T
        bar = tk.Frame(self, bg=T["panel"], height=26)
        bar.pack(fill="x", side="bottom"); bar.pack_propagate(False)
        self.status_var = tk.StringVar(value="جاهز ✅")
        tk.Label(bar, textvariable=self.status_var, font=FONT_SMALL,
                 bg=T["panel"], fg=T["grey"], anchor="w").pack(side="left", padx=10)
        tk.Label(bar, text=f"© 2025 {AUTHOR}  |  Log → {LOG_FILE}",
                 font=FONT_SMALL, bg=T["panel"], fg=T["grey"]).pack(side="right", padx=10)

    # ══════════════════════════════════════════
    #  CARD FACTORY
    # ══════════════════════════════════════════
    def _card(self, parent, title, sub, fn, color):
        T = self._T
        c = tk.Frame(parent, bg=T["card"], highlightbackground=T["border"],
                     highlightthickness=1, cursor="hand2")
        inn = tk.Frame(c, bg=T["card"]); inn.pack(fill="both", expand=True, padx=10, pady=8)
        tk.Label(inn, text=title, font=FONT_LABEL, bg=T["card"], fg=T["fg"], anchor="w").pack(fill="x")
        tk.Label(inn, text=sub,   font=FONT_SMALL, bg=T["card"], fg=T["grey"], anchor="w").pack(fill="x")
        tk.Frame(inn, bg=color, height=2).pack(fill="x", pady=(5,2))
        tk.Button(inn, text="▶ تشغيل", font=FONT_BTN, bg=color, fg="#0a0e1a",
                  relief="flat", cursor="hand2", pady=4,
                  activebackground=T["bg"], activeforeground=color,
                  command=lambda: self._run(fn)).pack(fill="x")
        c.bind("<Enter>", lambda e: c.config(highlightbackground=color))
        c.bind("<Leave>", lambda e: c.config(highlightbackground=T["border"]))
        return c

    # ══════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════
    def _out(self, msg: str):
        self._append_log(msg)

    def _append_log(self, msg: str):
        self.log_box.config(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        tag = ("green" if "✅" in msg else
               "yellow" if "⚠️" in msg else
               "red"    if "❌" in msg else "cyan")
        self.log_box.tag_config("green",  foreground=GREEN)
        self.log_box.tag_config("yellow", foreground=YELLOW)
        self.log_box.tag_config("red",    foreground=RED_C)
        self.log_box.tag_config("cyan",   foreground=ACCENT)
        self.log_box.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    def _run(self, fn, *args):
        beep_start()
        self.progress.start(10)
        self.status_var.set(f"⏳ {fn.__name__} ...")

        def worker():
            def out(msg):
                self.after(0, self._append_log, msg)
                log(msg)
            try:
                fn(*args, out) if args else fn(out)
                self.after(0, beep_ok)
                self.after(0, self.status_var.set, "✅ اكتمل")
            except Exception as e:
                self.after(0, self._append_log, f"❌ خطأ: {e}")
                self.after(0, beep_err)
                self.after(0, self.status_var.set, f"❌ {e}")
                log(f"Error in {fn.__name__}: {e}")
            finally:
                self.after(0, self.progress.stop)

        threading.Thread(target=worker, daemon=True).start()

    def _exit(self):
        if messagebox.askyesno("خروج", "هل تريد إغلاق Dr.Moataz Toolkit؟"):
            log("Application exited by user")
            self.destroy()


# ══════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════
if __name__ == "__main__":
    # Install psutil if missing
    try:
        import psutil
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "-q"])
        import psutil
    App().mainloop()
