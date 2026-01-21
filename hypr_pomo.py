import time
import subprocess
import sys
import re
import argparse
import json
import os
import random
import math
import select
import termios
import tty
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.live import Live
from rich.align import Align
from rich.table import Table
from rich.text import Text
from rich.box import SIMPLE, ROUNDED, DOUBLE
from rich.prompt import Prompt, IntPrompt, Confirm

# --- CONSTANTS & PATHS ---
APP_NAME = "HyprPomo"
VERSION = "v5.1"

# XDG Paths
CONFIG_DIR = Path.home() / ".config" / "hypr_pomo"
CONFIG_FILE = CONFIG_DIR / "config.json"
DATA_DIR = Path.home() / ".local" / "share" / "hypr_pomo"
DATA_FILE = DATA_DIR / "data.json"
WAYBAR_FILE = Path("/tmp/hypr_pomo_status")

# Default Configuration (Used if config.json is missing)
DEFAULT_CONFIG = {
    "times": {
        "work": "25m",
        "short_break": "5m",
        "long_break": "15m"
    },
    "colors": {
        "work": "cyan",
        "break": "magenta",
        "pause": "yellow",
        "dim": "bright_black"
    },
    "game_balance": {
        "xp_per_minute": 10,
        "overtime_multiplier": 2.0,
        "break_skip_xp_per_min": 5
    },
    "sounds": {
        "enabled": True,
        "work": "/usr/share/sounds/freedesktop/stereo/complete.oga",
        "break": "/usr/share/sounds/freedesktop/stereo/service-login.oga"
    }
}

QUOTES = [
    "Focus is the key to all success.",
    "Flow state loading...",
    "Discipline is freedom.",
    "Code is poetry.",
    "One brick at a time.",
    "Reality is created by the mind.",
    "Stay hungry, stay foolish.",
]

console = Console()

# --- CONFIG MANAGER ---

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self):
        """Loads config from JSON or creates it if missing."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists():
            self.save_config()
        else:
            try:
                with open(CONFIG_FILE, "r") as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
            except Exception as e:
                console.print(f"[red]Error loading config: {e}. Using defaults.[/]")

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
        except:
            pass

    def get(self, key, subkey=None):
        if subkey:
            return self.config.get(key, {}).get(subkey)
        return self.config.get(key)

# Global Config Instance
cfg = ConfigManager()

# --- UTILS ---

def parse_duration(duration_str):
    if not duration_str: return 25 * 60
    if isinstance(duration_str, int): return duration_str * 60
    if duration_str.isdigit(): return int(duration_str) * 60

    match = re.match(r"^(\d+)([smh])$", duration_str.lower())
    if match:
        v, u = match.groups()
        v = int(v)
        if u == 's': return v
        if u == 'm': return v * 60
        if u == 'h': return v * 3600
    return None

def send_notification(title, message):
    try:
        subprocess.run(["notify-send", "-a", APP_NAME, "-i", "alarm-clock", title, message])
    except:
        pass

def play_sound(sound_key):
    """Plays sound if enabled and file exists."""
    if not cfg.get("sounds", "enabled"): return

    path = cfg.get("sounds", sound_key)
    if path and os.path.exists(path):
        try:
            subprocess.Popen(["paplay", path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except:
            pass

def update_waybar(text):
    try:
        with open(WAYBAR_FILE, "w") as f:
            f.write(text)
    except:
        pass

def get_level_info(xp):
    level = math.floor(xp / 500) + 1
    xp_for_next = level * 500
    xp_in_level = xp - ((level - 1) * 500)
    return level, xp_in_level, 500

# --- INPUT HANDLING ---

class KeyReader:
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        try:
            tty.setcbreak(self.fd)
        except:
            pass
        return self

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def get_key(self):
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None

# --- DATA MANAGER ---

class DataManager:
    def __init__(self):
        self.ensure_file()
        self.refresh_daily_bounties()

    def ensure_file(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not DATA_FILE.exists():
            default_data = {
                "xp": 0,
                "history": [],
                "tasks": [],
                "bounties": {"date": "", "list": []}
            }
            with open(DATA_FILE, "w") as f:
                json.dump(default_data, f)

    def load(self):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {"xp": 0, "history": [], "tasks": [], "bounties": {"date": "", "list": []}}

    def save(self, data):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def refresh_daily_bounties(self):
        data = self.load()
        today = datetime.now().strftime("%Y-%m-%d")

        if data.get("bounties", {}).get("date") != today:
            possible_bounties = [
                {"id": "marathon", "text": "Marathon: Complete 4 sessions", "target": 4, "current": 0, "xp": 100},
                {"id": "deep_dive", "text": "Deep Dive: Complete a 45m+ session", "target": 45*60, "xp": 75},
                {"id": "early_bird", "text": "Early Bird: Finish a session before 9AM", "xp": 50},
                {"id": "night_owl", "text": "Night Owl: Finish a session after 8PM", "xp": 50},
                {"id": "iron_will", "text": "Iron Will: Complete a session without pausing", "xp": 60},
            ]
            todays_picks = random.sample(possible_bounties, 3)
            for b in todays_picks: b["completed"] = False

            data["bounties"] = {"date": today, "list": todays_picks}
            self.save(data)

    def check_bounties(self, session_context):
        data = self.load()
        bounties = data.get("bounties", {}).get("list", [])
        total_xp_gain = 0
        updates = False

        duration = session_context.get("duration", 0)
        paused = session_context.get("paused", False)
        now = datetime.now()

        for b in bounties:
            if b["completed"]: continue
            completed = False

            if b["id"] == "marathon":
                b["current"] = b.get("current", 0) + 1
                if b["current"] >= b["target"]: completed = True
                updates = True
            elif b["id"] == "deep_dive":
                if duration >= b["target"]: completed = True
            elif b["id"] == "early_bird":
                if now.hour < 9: completed = True
            elif b["id"] == "night_owl":
                if now.hour >= 20: completed = True
            elif b["id"] == "iron_will":
                if not paused: completed = True

            if completed:
                b["completed"] = True
                total_xp_gain += b["xp"]
                console.print(f"[bold yellow]📜 Bounty Completed: {b['text']} (+{b['xp']} XP)[/]")
                updates = True

        if updates:
            data["xp"] += total_xp_gain
            self.save(data)

        return total_xp_gain

    def add_xp(self, amount):
        data = self.load()
        data["xp"] += int(amount)
        self.save(data)
        return int(amount), data["xp"]

    def add_history(self, task_name, duration):
        data = self.load()
        entry = {
            "date": datetime.now().isoformat(),
            "task": task_name,
            "duration": duration
        }
        data["history"].append(entry)
        self.save(data)

    def add_task(self, task_name):
        data = self.load()
        new_id = 1
        if data["tasks"]:
            new_id = max(t["id"] for t in data["tasks"]) + 1
        data["tasks"].append({"id": new_id, "name": task_name, "completed": False})
        self.save(data)
        console.print(f"[green]Task added:[/ green] {task_name}")

    def list_tasks(self):
        data = self.load()
        tasks = [t for t in data["tasks"] if not t.get("completed")]
        return tasks

    def complete_task(self, task_id):
        data = self.load()
        found = False
        for t in data["tasks"]:
            if t["id"] == task_id:
                t["completed"] = True
                found = True
        self.save(data)
        return found

    def get_bounties(self):
        return self.load().get("bounties", {}).get("list", [])

# --- MAIN APP ---

class PomoApp:
    def __init__(self, work_sec, short_break_sec, long_break_sec, task_name="Focus", task_id=None):
        self.work_seconds_config = work_sec
        self.short_break_config = short_break_sec
        self.long_break_config = long_break_sec
        self.task_name = task_name
        self.task_id = task_id

        self.work_sessions = 0
        self.break_sessions = 0
        self.total_work_seconds = 0
        self.total_break_seconds = 0

        self.db = DataManager()
        self.quote = random.choice(QUOTES)

    def get_summary_table(self, current_mode, paused, overtime_secs=0):
        table = Table.grid(expand=True, padding=(0, 1))
        def fmt(seconds): return str(timedelta(seconds=int(seconds)))

        data = self.db.load()
        lvl, curr_xp, req_xp = get_level_info(data.get("xp", 0))

        # Colors from Config
        c_work = cfg.get("colors", "work")
        c_break = cfg.get("colors", "break")
        c_dim = cfg.get("colors", "dim")

        # XP Bar
        xp_bar = Progress(
            TextColumn(f"[bold yellow]Lvl {lvl}"),
            BarColumn(bar_width=None, complete_style="yellow", finished_style="yellow"),
            TextColumn(f"[dim]{curr_xp}/{req_xp} XP"),
            expand=True
        )
        xp_bar.add_task("xp", total=req_xp, completed=curr_xp)
        table.add_row(xp_bar)

        table.add_row(Text("Task :", style="bold white"), Text(self.task_name, style=f"bold {c_work}"))

        # CONTROLS TEXT
        if current_mode == "work" and overtime_secs > 0:
            controls = f"[bold {c_work}]🌊 FLOW MODE (+2x XP)[/] [dim]press 'b' to break[/]"
        elif current_mode == "work":
            controls = "[dim]p:pause s:skip q:quit[/]"
        else:
            controls = "[dim]s:skip (rewards XP) q:quit[/]"

        if paused:
            controls = "[bold yellow]PAUSED[/]"

        table.add_row(Align.center(controls))
        table.add_row(Text("", style="dim"), Text("", style="dim"))

        w_style = f"bold {c_work}" if current_mode == "work" else "dim white"
        table.add_row(Text("Work :", style=w_style), Text(f"{fmt(self.total_work_seconds)} ({self.work_sessions})", style=w_style))

        b_style = f"bold {c_break}" if current_mode != "work" else "dim white"
        table.add_row(Text("Break:", style=b_style), Text(f"{fmt(self.total_break_seconds)} ({self.break_sessions})", style=b_style))

        return table

    def run_timer(self, total_seconds, mode):
        start_time = time.time()

        c_work = cfg.get("colors", "work")
        c_break = cfg.get("colors", "break")
        c_pause = cfg.get("colors", "pause")
        c_dim = cfg.get("colors", "dim")

        color = c_work if mode == "work" else c_break
        icon = "🍅" if mode == "work" else "☕"

        play_sound(mode)

        progress = Progress(
            TextColumn(f"[{color}]{icon}"),
            BarColumn(bar_width=None, complete_style=color, finished_style="green"),
            TextColumn(f"[bold {color}]{{task.percentage:>3.0f}}%"),
            TextColumn(f"[{color}]{mode.upper()}"),
            TimeRemainingColumn(),
            expand=True
        )

        task_id = progress.add_task("timer", total=total_seconds)

        paused = False
        skipped = False
        overtime_active = False
        overtime_start = 0
        current_overtime = 0
        remaining_at_skip = 0

        with KeyReader() as keys:
            with Live(console=console, refresh_per_second=4) as live:
                while True:
                    # INPUT
                    key = keys.get_key()
                    if key:
                        k = key.lower()
                        if k == 'q':
                            update_waybar("")
                            sys.exit(0)
                        elif k == 's' and not overtime_active:
                            skipped = True
                            remaining_at_skip = max(0, total_seconds - (time.time() - start_time))
                            break
                        elif k == 'p' and not overtime_active:
                            paused = not paused
                            desc = f"[{c_pause if paused else color}]{'PAUSED' if paused else mode.upper()}"
                            progress.update(task_id, description=desc)
                        elif k == 'b' and overtime_active:
                            break

                    # LOGIC
                    if paused:
                        time.sleep(0.1)
                        start_time += 0.1
                        ui = Table.grid(expand=True)
                        ui.add_row(Panel(self.get_summary_table(mode, True), border_style=c_pause))
                        ui.add_row(Panel(progress, border_style=c_pause))
                        live.update(Align.center(ui, vertical="middle"))
                        continue

                    elapsed = time.time() - start_time
                    if mode == "work": self.total_work_seconds += 0.25
                    else: self.total_break_seconds += 0.25

                    # OVERTIME LOGIC
                    if mode == "work" and elapsed >= total_seconds:
                        if not overtime_active:
                            overtime_active = True
                            overtime_start = time.time()
                            progress.update(task_id, total=None, completed=0, description=f"[bold {c_work}]🌊 FLOW")

                        current_overtime = time.time() - overtime_start
                        ot_str = str(timedelta(seconds=int(current_overtime)))[2:]
                        update_waybar(f"🌊 +{ot_str}")

                        ui = Table.grid(expand=True)
                        ui.add_row(Panel(self.get_summary_table(mode, False, current_overtime), border_style=c_work))
                        ui.add_row(Panel(Align.center(f"[bold {c_work} size=20]+{ot_str}[/]\n[dim]Flow State active. Press 'b' to break.[/]"), border_style=c_work))
                        live.update(Align.center(ui, vertical="middle"))
                        time.sleep(0.1)
                        continue

                    # NORMAL TIMER LOGIC
                    if not overtime_active:
                        if elapsed >= total_seconds:
                            break

                        progress.update(task_id, completed=elapsed)
                        remaining = max(0, total_seconds - elapsed)
                        rem_str = str(timedelta(seconds=int(remaining)))[2:]
                        waybar_icon = "🍅" if mode == "work" else "☕"
                        update_waybar(f"{waybar_icon} {rem_str}")

                        summary = Panel(self.get_summary_table(mode, False), title="[bold white]Session Info", border_style=c_dim, box=SIMPLE, padding=(0, 1))
                        timer_panel = Panel(progress, border_style=color, padding=(1, 2))

                        ui = Table.grid(expand=True)
                        ui.add_row(summary)
                        ui.add_row(timer_panel)
                        live.update(Align.center(ui, vertical="middle"))

                    time.sleep(0.1)

        return skipped, current_overtime, remaining_at_skip

    def start(self):
        console.clear()
        update_waybar("")

        try:
            while True:
                # --- WORK PHASE ---
                send_notification("Focus", f"Time to work on: {self.task_name}")
                skipped, overtime, _ = self.run_timer(self.work_seconds_config, "work")

                if not skipped:
                    xp_rate = cfg.get("game_balance", "xp_per_minute")
                    ot_mult = cfg.get("game_balance", "overtime_multiplier")

                    base_mins = self.work_seconds_config / 60
                    ot_mins = overtime / 60

                    xp_base = base_mins * xp_rate
                    xp_ot = ot_mins * xp_rate * ot_mult

                    total_xp, _ = self.db.add_xp(xp_base + xp_ot)
                    self.db.add_history(self.task_name, self.work_seconds_config + overtime)
                    self.work_sessions += 1

                    context = {"duration": self.work_seconds_config + overtime, "paused": False}
                    bounty_xp = self.db.check_bounties(context)

                    msg = f"[bold green]Session Complete![/]\nBase: {int(xp_base)} XP"
                    if xp_ot > 0: msg += f" | Flow Bonus: [cyan]+{int(xp_ot)} XP[/]"
                    if bounty_xp > 0: msg += f" | Bounties: [yellow]+{int(bounty_xp)} XP[/]"

                    console.print(msg)

                    if self.task_id is not None:
                        play_sound("work")
                        if Confirm.ask(f"Did you finish [cyan]{self.task_name}[/]?"):
                            self.db.complete_task(self.task_id)
                            console.print("[bold green]Task Complete![/]")
                            self.task_id = None
                            self.task_name = "General Focus"
                    time.sleep(2)

                # --- BREAK PHASE ---
                is_long = self.work_sessions % 4 == 0
                base_break = self.long_break_config if is_long else self.short_break_config

                total_break = base_break + overtime
                label = "long_break" if is_long else "short_break"

                send_notification("Break", f"Time to relax. ({int(total_break/60)}m)")

                skipped_break, _, rem_break = self.run_timer(total_break, label)

                if skipped_break and rem_break > 60:
                    skip_rate = cfg.get("game_balance", "break_skip_xp_per_min")
                    mins_saved = rem_break / 60
                    xp_gain = int(mins_saved * skip_rate)
                    self.db.add_xp(xp_gain)
                    console.print(f"[bold magenta]Break Skipped! +{xp_gain} XP for getting back to work![/]")
                    time.sleep(1.5)

                self.break_sessions += 1

        except KeyboardInterrupt:
            console.print(f"\n[red]Timer stopped.[/]")
            update_waybar("")

# --- COMMANDS ---

def cmd_help():
    table = Table(title=f"🍅 {APP_NAME} Help", box=ROUNDED, border_style="cyan")
    table.add_column("Command / Key", style="yellow")
    table.add_column("Description", style="white")

    table.add_row("timer", "Start timer (interactive)")
    table.add_row("timer 45m", "Start 45m session")
    table.add_row("timer add <name>", "Add a new task")
    table.add_row("timer list", "Show tasks, stats, and bounties")
    table.add_row("timer done <id>", "Complete a task manually")
    table.add_row("timer help", "Show this screen")
    table.add_section()
    table.add_row("p", "Pause/Resume timer")
    table.add_row("s", "Skip current session (break skip gives XP)")
    table.add_row("b", "Break flow state (end overtime)")
    table.add_row("q", "Quit application")

    console.print(table)
    console.print(f"\n[dim]Config file located at: {CONFIG_FILE}[/]")

def cmd_list(db):
    data = db.load()
    lvl, curr, req = get_level_info(data.get("xp", 0))
    bounties = db.get_bounties()
    tasks = db.list_tasks()

    console.print(Panel(f"[bold yellow]Level {lvl}[/]\nXP: {curr}/{req}", title="Player Stats", border_style="cyan"))

    b_table = Table(title="📜 Daily Bounties", box=SIMPLE, show_header=False)
    for b in bounties:
        status = "[green]✔[/]" if b["completed"] else "[dim]○[/]"
        b_table.add_row(status, b["text"], f"[yellow]+{b['xp']} XP[/]")
    console.print(b_table)

    console.print("")
    if not tasks:
        console.print("[dim]No active tasks. Use 'timer add <name>' to create one.[/]")
    else:
        t_table = Table(title="📝 Pending Tasks", box=ROUNDED, border_style="white")
        t_table.add_column("ID", style="cyan", justify="right")
        t_table.add_column("Task Name", style="white")
        for t in tasks:
            t_table.add_row(str(t['id']), t['name'])
        console.print(t_table)

def cmd_add(db, name):
    db.add_task(name)

def cmd_done(db, task_id_str):
    try:
        t_id = int(task_id_str)
        if db.complete_task(t_id):
            console.print(f"[green]Task {t_id} marked as complete![/]")
        else:
            console.print(f"[red]Task {t_id} not found.[/]")
    except ValueError:
        console.print("[red]Please provide a valid numeric ID.[/]")

# --- ENTRY POINT ---

if __name__ == "__main__":
    db = DataManager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        args = sys.argv[2:]

        if cmd == "help":
            cmd_help()
            sys.exit(0)

        if cmd == "add":
            if not args: console.print("[red]Usage: timer add \"Task Name\"[/]")
            else: cmd_add(db, " ".join(args))
            sys.exit(0)

        if cmd == "list":
            cmd_list(db)
            sys.exit(0)

        if cmd in ["done", "finish"]:
            if not args: console.print("[red]Usage: timer done <Task ID>[/]")
            else: cmd_done(db, args[0])
            sys.exit(0)

    # Normal Start Logic
    tasks = db.list_tasks()
    selected_task_name = "General Focus"
    selected_task_id = None

    # Task Selection
    if len(sys.argv) == 1 and tasks:
        console.print("[bold cyan]Select a task:[/]")
        for t in tasks:
            console.print(f" [cyan]{t['id']}[/]: {t['name']}")
        console.print(" [dim]0: Custom / General[/]")

        choice = IntPrompt.ask("Enter ID", default=0)
        if choice != 0:
            found = next((t for t in tasks if t['id'] == choice), None)
            if found:
                selected_task_name = found['name']
                selected_task_id = found['id']

    start_args = sys.argv[1:]
    times = []
    task_parts = []
    for arg in start_args:
        d = parse_duration(arg)
        if d: times.append(d)
        else: task_parts.append(arg)

    if task_parts:
        selected_task_name = " ".join(task_parts)
        selected_task_id = None

    # Load defaults from Config if not provided
    def_work = parse_duration(cfg.get("times", "work"))
    def_short = parse_duration(cfg.get("times", "short_break"))
    def_long = parse_duration(cfg.get("times", "long_break"))

    w_sec = times[0] if len(times) >= 1 else def_work
    s_sec = times[1] if len(times) >= 2 else def_short
    l_sec = times[2] if len(times) >= 3 else def_long

    app = PomoApp(w_sec, s_sec, l_sec, selected_task_name, selected_task_id)
    app.start()
