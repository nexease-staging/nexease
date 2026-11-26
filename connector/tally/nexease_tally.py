"""NexEase Tally Connector.

Runs on the computer where TallyPrime is open and keeps it in sync with NexEase:
- asks NexEase what to do (every 30 seconds by default),
- sends each request to Tally on this computer (http://localhost:9000) and returns Tally's reply.

All sync logic lives on the NexEase server, so this app is a small, safe relay. It only ever talks
to Tally on this computer and to your NexEase server; no Tally data is stored here.

Python standard library only. Build a Windows .exe with PyInstaller (see build workflow).
Usage:
    NexEase-Tally-Connector.exe                 window
    NexEase-Tally-Connector.exe --headless      no window (after pairing), e.g. at Windows start-up
    nexease_tally.py --pair CODE --server URL   pair without the window
    nexease_tally.py --once                     one sync round, then exit (for testing)
"""
import argparse
import base64
import gzip
import json
import os
import platform
import queue
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime

VERSION = "1.0.0"
DEFAULT_SERVER = "https://nexease-backend-singapore.onrender.com/api/v1"
DEFAULT_TALLY = "http://localhost:9000"
DEFAULT_APP = "https://nexease-frontend-singapore.onrender.com"
APP_NAME = "NexEase Tally Connector"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# --------------------------------------------------------------------------------------------
# Settings on this computer
# --------------------------------------------------------------------------------------------

def config_dir():
    base = os.environ.get("NEXEASE_TALLY_HOME") or (os.path.join(os.environ.get("APPDATA", ""), "NexEase Tally") if os.name == "nt" else os.path.expanduser("~/.nexease-tally"))
    os.makedirs(base, exist_ok=True)
    return base


def load_config():
    path = os.path.join(config_dir(), "config.json")
    cfg = {"server": DEFAULT_SERVER, "tally_url": DEFAULT_TALLY, "token": "", "device_name": platform.node() or "Tally computer", "interval": 30,
           "tally_exe": "", "auto_start_tally": False, "organization": ""}
    try:
        with open(path, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    path = os.path.join(config_dir(), "config.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    os.replace(tmp, path)


def log_line(message):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {message}"
    try:
        path = os.path.join(config_dir(), "connector.log")
        if os.path.exists(path) and os.path.getsize(path) > 2_000_000:
            os.replace(path, path + ".1")
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    return line


# --------------------------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------------------------

class ServerError(Exception):
    def __init__(self, message, status=0):
        super().__init__(message)
        self.status = status


def post_json(url, data, token=None, timeout=60):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json", "User-Agent": f"NexEaseTally/{VERSION}",
                                                                      **({"X-NexEase-Device": token} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            message = json.loads(e.read().decode("utf-8")).get("error") or str(e)
        except ValueError:
            message = str(e)
        raise ServerError(message, e.code)
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise ServerError(f"Cannot reach NexEase: {getattr(e, 'reason', e)}")


def tally_post(tally_url, xml, timeout=300):
    """Send one XML request to Tally. Tally expects UTF-8 (UTF-16 replies are decoded too)."""
    req = urllib.request.Request(tally_url, data=xml.encode("utf-8"), method="POST", headers={"Content-Type": "text/xml;charset=utf-8"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    for enc in ("utf-8", "utf-16"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def tally_alive(tally_url, timeout=5):
    try:
        with urllib.request.urlopen(urllib.request.Request(tally_url, method="GET"), timeout=timeout) as resp:
            text = resp.read(200).decode("utf-8", "ignore")
            return True, ("TallyPrime" if "Tally" in text else "Tally")
    except urllib.error.HTTPError:
        return True, "Tally"
    except (urllib.error.URLError, OSError) as e:
        return False, f"Tally is not reachable at {tally_url} ({getattr(e, 'reason', e)}). Open Tally and enable Client/Server on port 9000."


# --------------------------------------------------------------------------------------------
# Sync engine
# --------------------------------------------------------------------------------------------

class Connector:
    def __init__(self, cfg, on_event=None):
        self.cfg = cfg
        self.on_event = on_event or (lambda kind, message: None)
        self.stop_flag = threading.Event()
        self.wake = threading.Event()
        self.paused = False
        self.stats = {"jobs": 0, "failed": 0, "last_sync": None, "tally": "", "server": ""}
        self.last_tally_start = 0

    def emit(self, kind, message):
        self.on_event(kind, log_line(message) if kind in ("log", "error") else message)

    def url(self, path):
        return self.cfg["server"].rstrip("/") + "/business/tally/agent/" + path

    def pair(self, code, server=None):
        if server:
            self.cfg["server"] = server.strip().rstrip("/")
        ok, tally_info = tally_alive(self.cfg["tally_url"])
        result = post_json(self.url("pair/"), {"code": code, "name": self.cfg["device_name"], "info": self.info(ok, tally_info)})
        self.cfg["token"] = result["token"]
        self.cfg["organization"] = result.get("organization", "")
        self.cfg["interval"] = int(result.get("interval") or self.cfg.get("interval") or 30)
        save_config(self.cfg)
        self.emit("log", f"Paired with {self.cfg['organization'] or 'NexEase'}.")
        return result

    def info(self, tally_ok, detail):
        return {"version": VERSION, "tally_url": self.cfg["tally_url"], "tally_ok": bool(tally_ok), "tally_version": detail if tally_ok else "",
                "os": f"{platform.system()} {platform.release()}", "interval": self.cfg.get("interval", 30), "error": "" if tally_ok else detail}

    def maybe_start_tally(self):
        exe = self.cfg.get("tally_exe")
        if self.cfg.get("auto_start_tally") and exe and os.path.exists(exe) and time.time() - self.last_tally_start > 300:
            self.last_tally_start = time.time()
            try:
                subprocess.Popen([exe], cwd=os.path.dirname(exe))
                self.emit("log", "Started Tally.")
            except OSError as e:
                self.emit("error", f"Could not start Tally: {e}")

    def run_once(self):
        """One round: heartbeat, then run every job NexEase hands out until the queue is empty."""
        tally_ok, detail = tally_alive(self.cfg["tally_url"])
        self.stats["tally"] = "Connected" if tally_ok else detail
        self.emit("tally", self.stats["tally"])
        if not tally_ok:
            self.maybe_start_tally()
        rounds = 0
        while not self.stop_flag.is_set() and rounds < 50:
            rounds += 1
            reply = post_json(self.url("poll/"), {"info": self.info(tally_ok, detail), "max_jobs": 8}, self.cfg["token"])
            self.stats["server"] = "Connected"
            self.emit("server", "Connected")
            if reply.get("interval"):
                self.cfg["interval"] = int(reply["interval"])
            jobs = reply.get("jobs") or []
            real = [j for j in jobs if j.get("type") != "companies"]
            for job in jobs:
                self.run_job(job)
            self.stats["last_sync"] = datetime.now()
            self.emit("synced", self.stats["last_sync"].strftime("%H:%M:%S"))
            if not real:
                break
        return True

    def run_job(self, job):
        started = time.time()
        try:
            body = tally_post(self.cfg["tally_url"], job["xml"])
            packed = base64.b64encode(gzip.compress(body.encode("utf-8"))).decode("ascii")
            result = post_json(self.url(f"jobs/{job['id']}/"), {"ok": True, "body": packed, "encoding": "gzip+base64", "ms": int((time.time() - started) * 1000)}, self.cfg["token"], timeout=180)
        except (urllib.error.URLError, OSError) as e:
            self.stats["failed"] += 1
            post_json(self.url(f"jobs/{job['id']}/"), {"ok": False, "error": f"Tally did not answer: {getattr(e, 'reason', e)}"}, self.cfg["token"])
            self.emit("error", f"Tally did not answer ({job.get('type')}): {getattr(e, 'reason', e)}")
            return
        self.stats["jobs"] += 1
        if result.get("status") == "failed":
            self.stats["failed"] += 1
            self.emit("error", f"{result.get('label') or job.get('type')}: {result.get('error', 'failed')}")
        elif job.get("type") == "push":
            self.emit("log", f"Sent to Tally: {result.get('label') or 'entry'}")
        elif job.get("type") == "pull" and result.get("received"):
            self.emit("log", f"Received {result['received']} {result.get('label', 'records')} from Tally")

    def loop(self):
        self.emit("log", f"{APP_NAME} {VERSION} started. Tally: {self.cfg['tally_url']}")
        backoff = 0
        while not self.stop_flag.is_set():
            if not self.paused and self.cfg.get("token"):
                try:
                    self.run_once()
                    backoff = 0
                except ServerError as e:
                    self.stats["server"] = str(e)
                    self.emit("server", str(e))
                    if e.status == 401:
                        self.emit("error", "This connector was removed in NexEase. Pair it again.")
                        self.cfg["token"] = ""
                        save_config(self.cfg)
                        self.emit("unpaired", "")
                    else:
                        self.emit("error", str(e))
                    backoff = min(backoff + 1, 6)
                except Exception as e:  # keep running whatever happens
                    self.emit("error", f"Unexpected problem: {e}")
                    backoff = min(backoff + 1, 6)
            wait = max(10, int(self.cfg.get("interval") or 30)) * (1 + backoff)
            self.wake.wait(wait)
            self.wake.clear()

    def start(self):
        threading.Thread(target=self.loop, daemon=True).start()

    def sync_now(self):
        self.wake.set()


# --------------------------------------------------------------------------------------------
# Windows start-up
# --------------------------------------------------------------------------------------------

def set_autostart(enabled):
    if os.name != "nt":
        return False
    import winreg
    exe = sys.executable if getattr(sys, "frozen", False) else f'"{sys.executable}" "{os.path.abspath(__file__)}"'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe}" --headless' if getattr(sys, "frozen", False) else f"{exe} --headless")
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    return True


def autostart_enabled():
    if os.name != "nt":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except OSError:
        return False


# --------------------------------------------------------------------------------------------
# Window
# --------------------------------------------------------------------------------------------

def run_window(cfg):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    events = queue.Queue()
    conn = Connector(cfg, on_event=lambda kind, message: events.put((kind, message)))
    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("560x520")
    root.minsize(500, 460)
    navy, ink, muted, good, bad = "#14234B", "#1d2433", "#6b7280", "#15803d", "#b91c1c"
    root.configure(bg="white")
    style = ttk.Style()
    try:
        style.theme_use("vista" if os.name == "nt" else "clam")
    except tk.TclError:
        pass
    style.configure("TLabel", background="white", foreground=ink, font=("Segoe UI", 10))
    style.configure("Muted.TLabel", foreground=muted, font=("Segoe UI", 9))
    style.configure("Head.TLabel", foreground=navy, font=("Segoe UI Semibold", 15))
    style.configure("TFrame", background="white")
    style.configure("TCheckbutton", background="white")

    header = tk.Frame(root, bg=navy, height=56)
    header.pack(fill="x")
    tk.Label(header, text="NexEase  ⇄  Tally", bg=navy, fg="white", font=("Segoe UI Semibold", 14)).pack(side="left", padx=18, pady=14)
    tk.Label(header, text=f"v{VERSION}", bg=navy, fg="#c7d2fe", font=("Segoe UI", 9)).pack(side="right", padx=18)
    body = ttk.Frame(root, padding=18)
    body.pack(fill="both", expand=True)

    # ---- pairing page
    pair_page = ttk.Frame(body)
    ttk.Label(pair_page, text="Connect this computer's Tally to NexEase", style="Head.TLabel").pack(anchor="w")
    ttk.Label(pair_page, text="In NexEase open Tally → Connect, copy the pairing code and enter it here.", style="Muted.TLabel", wraplength=500).pack(anchor="w", pady=(4, 16))
    ttk.Label(pair_page, text="Pairing code").pack(anchor="w")
    code_var = tk.StringVar()
    code_entry = ttk.Entry(pair_page, textvariable=code_var, font=("Consolas", 16), width=14)
    code_entry.pack(anchor="w", pady=(2, 12))
    ttk.Label(pair_page, text="Computer name (shown in NexEase)").pack(anchor="w")
    name_var = tk.StringVar(value=cfg["device_name"])
    ttk.Entry(pair_page, textvariable=name_var, width=40).pack(anchor="w", pady=(2, 12))
    adv = ttk.Frame(pair_page)
    ttk.Label(adv, text="NexEase server").grid(row=0, column=0, sticky="w")
    server_var = tk.StringVar(value=cfg["server"])
    ttk.Entry(adv, textvariable=server_var, width=52).grid(row=1, column=0, sticky="w", pady=(2, 8))
    ttk.Label(adv, text="Tally address").grid(row=2, column=0, sticky="w")
    tally_var = tk.StringVar(value=cfg["tally_url"])
    ttk.Entry(adv, textvariable=tally_var, width=30).grid(row=3, column=0, sticky="w", pady=(2, 8))
    adv.pack(anchor="w", pady=(0, 8))
    pair_msg = ttk.Label(pair_page, text="", style="Muted.TLabel", wraplength=500)
    pair_msg.pack(anchor="w", pady=(4, 8))

    def do_pair():
        code = code_var.get().strip()
        if not code:
            pair_msg.configure(text="Enter the pairing code from NexEase.", foreground=bad)
            return
        cfg["device_name"] = name_var.get().strip() or cfg["device_name"]
        cfg["tally_url"] = tally_var.get().strip() or DEFAULT_TALLY
        pair_msg.configure(text="Connecting…", foreground=muted)
        root.update_idletasks()
        try:
            conn.pair(code, server_var.get())
        except ServerError as e:
            pair_msg.configure(text=str(e), foreground=bad)
            return
        show_status()
        conn.sync_now()

    ttk.Button(pair_page, text="Connect", command=do_pair).pack(anchor="w")

    # ---- status page
    status_page = ttk.Frame(body)
    org_label = ttk.Label(status_page, text="", style="Head.TLabel")
    org_label.pack(anchor="w")
    grid = ttk.Frame(status_page)
    grid.pack(fill="x", pady=(10, 8))
    rows = {}
    for i, (key, label) in enumerate([("tally", "Tally"), ("server", "NexEase"), ("synced", "Last sync"), ("jobs", "Processed")]):
        ttk.Label(grid, text=label, style="Muted.TLabel").grid(row=i, column=0, sticky="w", pady=3)
        rows[key] = ttk.Label(grid, text="…")
        rows[key].grid(row=i, column=1, sticky="w", padx=14)
    buttons = ttk.Frame(status_page)
    buttons.pack(fill="x", pady=(4, 10))
    pause_btn = ttk.Button(buttons, text="Pause")
    ttk.Button(buttons, text="Sync now", command=conn.sync_now).pack(side="left")
    pause_btn.pack(side="left", padx=6)
    ttk.Button(buttons, text="Open NexEase", command=lambda: webbrowser.open(cfg.get("app_url") or DEFAULT_APP + "/tally")).pack(side="left")

    def toggle_pause():
        conn.paused = not conn.paused
        pause_btn.configure(text="Resume" if conn.paused else "Pause")
        rows["synced"].configure(text="Paused" if conn.paused else "…")
    pause_btn.configure(command=toggle_pause)

    opts = ttk.Frame(status_page)
    opts.pack(fill="x", pady=(0, 8))
    auto_var = tk.BooleanVar(value=autostart_enabled())
    ttk.Checkbutton(opts, text="Start with Windows (runs in the background)", variable=auto_var, command=lambda: set_autostart(auto_var.get())).pack(anchor="w")
    tally_auto = tk.BooleanVar(value=bool(cfg.get("auto_start_tally")))

    def toggle_tally_auto():
        if tally_auto.get() and not cfg.get("tally_exe"):
            exe = filedialog.askopenfilename(title="Choose tally.exe", filetypes=[("Tally", "tally.exe"), ("Programs", "*.exe")])
            if not exe:
                tally_auto.set(False)
                return
            cfg["tally_exe"] = exe
        cfg["auto_start_tally"] = tally_auto.get()
        save_config(cfg)
    ttk.Checkbutton(opts, text="Open Tally automatically if it is closed", variable=tally_auto, command=toggle_tally_auto).pack(anchor="w")

    ttk.Label(status_page, text="Activity", style="Muted.TLabel").pack(anchor="w")
    log_box = tk.Text(status_page, height=10, font=("Consolas", 9), relief="flat", bg="#f6f7fb", fg=ink, wrap="word")
    log_box.pack(fill="both", expand=True)
    log_box.tag_configure("error", foreground=bad)

    def unpair():
        if messagebox.askyesno(APP_NAME, "Disconnect this computer from NexEase? Sync stops until you pair again."):
            cfg["token"] = ""
            save_config(cfg)
            show_pair()
    ttk.Button(status_page, text="Disconnect", command=unpair).pack(anchor="e", pady=(8, 0))

    def show_pair():
        status_page.pack_forget()
        pair_page.pack(fill="both", expand=True)
        code_entry.focus_set()

    def show_status():
        pair_page.pack_forget()
        status_page.pack(fill="both", expand=True)
        org_label.configure(text=cfg.get("organization") or "Connected to NexEase")

    def pump():
        while True:
            try:
                kind, message = events.get_nowait()
            except queue.Empty:
                break
            if kind == "tally":
                rows["tally"].configure(text=message, foreground=good if message == "Connected" else bad)
            elif kind == "server":
                rows["server"].configure(text=message, foreground=good if message == "Connected" else bad)
            elif kind == "synced":
                rows["synced"].configure(text=message, foreground=ink)
                rows["jobs"].configure(text=f"{conn.stats['jobs']} requests · {conn.stats['failed']} problems")
            elif kind == "unpaired":
                show_pair()
            elif kind in ("log", "error"):
                log_box.insert("end", message + "\n", "error" if kind == "error" else "")
                if int(log_box.index("end-1c").split(".")[0]) > 400:
                    log_box.delete("1.0", "100.0")
                log_box.see("end")
        root.after(400, pump)

    show_status() if cfg.get("token") else show_pair()
    conn.start()
    pump()
    root.mainloop()
    conn.stop_flag.set()


def main(argv=None):
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--headless", action="store_true", help="run without a window")
    parser.add_argument("--once", action="store_true", help="one sync round, then exit")
    parser.add_argument("--pair", metavar="CODE", help="pair with this code")
    parser.add_argument("--server", help="NexEase API address")
    parser.add_argument("--tally", help="Tally address, default http://localhost:9000")
    args = parser.parse_args(argv)
    cfg = load_config()
    if args.tally:
        cfg["tally_url"] = args.tally
    if args.server:
        cfg["server"] = args.server.rstrip("/")
    conn = Connector(cfg, on_event=lambda kind, message: print(message) if kind in ("log", "error") else None)
    if args.pair:
        try:
            conn.pair(args.pair, args.server)
        except ServerError as e:
            print(f"Pairing failed: {e}", file=sys.stderr)
            return 2
        if not (args.once or args.headless):
            return 0
    if args.once:
        if not cfg.get("token"):
            print("Not paired. Run with --pair CODE first.", file=sys.stderr)
            return 2
        try:
            conn.run_once()
        except ServerError as e:
            print(f"Sync failed: {e}", file=sys.stderr)
            return 1
        return 0
    if args.headless:
        if not cfg.get("token"):
            print("Not paired. Open the connector window and pair first.", file=sys.stderr)
            return 2
        conn.loop()
        return 0
    run_window(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
