HyprPomo (v5.3) 

A high-performance, gamified Pomodoro timer designed for Hyprland and CLI power users. This tool combines productivity tracking with RPG elements to keep you focused. 

Quick Install (One-Line) 

Copy and paste this into your terminal to install HyprPomo automatically: 

```bash
curl -sL https://raw.githubusercontent.com/SamuelSmthSmth/HyprPomo/main/install.sh | bash

```



**This script will:**

* Install dependencies (rich). 


* Download `hypr_pomo.py` to `~/.local/bin/`. 


* Create a timer alias for your shell (Fish, Bash, or Zsh). 


* Create default config files. 



---

Manual Installation 

If you prefer to install it yourself: 

1. 
**Download the script:** Download `hypr_pomo.py` and place it somewhere in your PATH (e.g., `~/.local/bin/`). 


2. 
**Install Dependencies:** Run `pip3 install rich`. 


3. 
**Create an Alias:** Add the following to your shell config (`~/.bashrc`, `~/.zshrc`, or `~/.config/fish/config.fish`): 



**For Bash/Zsh:**

```bash
alias timer="python3 /path/to/hypr_pomo.py"

```



**For Fish:**

```fish
function timer
    python3 /path/to/hypr_pomo.py $argv
end

```



---

Features 

* **Gamification:** Earn XP for every minute of work. Level up every 500 XP. 


* 
**Flow Mode:** When the timer hits 00:00, it enters "Flow State" instead of ringing immediately. It counts up, granting 2x XP for overtime and adding that time to your upcoming break. 


* 
**Daily Bounties:** The system generates 3 random challenges every day to keep things fresh. 


* 
**Task Management:** Integrated todo list to track specific objectives. 


* 
**Waybar Support:** Writes status to a temporary file for easy integration with system bars. 


* 
**Zen Mode:** A centered, distraction-free command line interface. 



---

Controls 

These controls apply while the timer is running: 

| Key | Action | Description |
| --- | --- | --- |
| **p** | Pause / Resume | Pauses the timer. Note: Pausing may fail certain bounties (Iron Will). 

 |
| **s** | Skip | Skips the current session. If used during a break, you gain bonus XP for returning to work early. 

 |
| **b** | Break Flow | Only active during Flow Mode (Overtime). Ends the session and triggers the break. 

 |
| **q** | Quit | Exits the application immediately. 

 |

---

Usage Commands 

| Command | Description |
| --- | --- |
| `timer` | Start a standard session (Default: 25m Work / 5m Break). 

 |
| `timer <time>` | Start a custom duration session (e.g., `timer 45m`, `timer 1h`). 

 |
| `timer add <name>` | Add a task to your pending list. 

 |
| `timer list` | View your Level, XP, current Daily Bounties, and pending tasks. 

 |
| `timer done <id>` | Mark a specific task ID as complete. 

 |
| `timer help` | Show the built-in manual. 

 |

---

Game Mechanics 

XP System 

* 
**Standard Work:** 10 XP per minute. 


* 
**Flow Mode (Overtime):** 20 XP per minute (2x Multiplier). 


* 
**Skipping Break:** 5 XP per minute saved. 



Daily Bounties 

Three of the following are selected randomly each day (reset at midnight): 

* 
**Marathon:** Complete 4 sessions in one day (100 XP). 


* 
**Deep Dive:** Complete a single session longer than 45 minutes (75 XP). 


* 
**Early Bird:** Finish a session before 9:00 AM (50 XP). 


* 
**Night Owl:** Finish a session after 8:00 PM (50 XP). 


* 
**Iron Will:** Complete a session without pausing a single time (60 XP). 



---

Configuration 

On the first run, a configuration file is generated at: `~/.config/hypr_pomo/config.json` 

You can modify this file to customize defaults: 

```json
{
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
        "enabled": true,
        "work": "/usr/share/sounds/freedesktop/stereo/complete.oga",
        "break": "/usr/share/sounds/freedesktop/stereo/service-login.oga"
    }
}

```



---

Waybar Integration 

The script writes the current timer status (e.g., "WORK 24:59" or "FLOW +01:30") to `/tmp/hypr_pomo_status`. 

1. Add to `~/.config/waybar/modules.json`: 

```json
"custom/pomo": {
    "exec": "cat /tmp/hypr_pomo_status 2>/dev/null",
    "interval": 1,
    "format": "{}",
    "on-click": "timer"
}

```



2. Add to `~/.config/waybar/config`: Add `"custom/pomo"` to your `modules-left`, `modules-center`, or `modules-right` array. 

---

Data Storage 

Your user history, accumulated XP, current level, and active tasks are stored in JSON format at: `~/.local/share/hypr_pomo/data.json` 
