#!/usr/bin/env python3
import curses
import json
import subprocess
import time
import urllib.request
import urllib.error
import datetime

def get_agy_ports():
    ports = []
    try:
        cmd = "ss -tlnp 2>/dev/null | grep agy"
        output = subprocess.check_output(cmd, shell=True, text=True)
        for line in output.split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 4:
                    addr_port = parts[3]
                    port = int(addr_port.split(':')[-1])
                    ports.append(port)
    except Exception:
        pass
        
    if not ports:
        try:
            cmd = "lsof -i -P -n 2>/dev/null | grep agy | grep LISTEN"
            output = subprocess.check_output(cmd, shell=True, text=True)
            for line in output.split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        addr = parts[-2]
                        port = int(addr.split(':')[-1])
                        ports.append(port)
        except Exception:
            pass
    return list(set(ports))

def fetch_quota_data(port):
    url = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
    req = urllib.request.Request(url, data=b"{}", headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=1) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None

def get_quota():
    ports = get_agy_ports()
    for port in ports:
        data = fetch_quota_data(port)
        if data:
            return data
    return None

def format_reset_time(reset_time):
    if reset_time == "Unknown":
        return "Unknown"
    try:
        reset_dt = datetime.datetime.strptime(reset_time, "%Y-%m-%dT%H:%M:%SZ")
        now_dt = datetime.datetime.utcnow()
        if reset_dt > now_dt:
            diff = reset_dt - now_dt
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if diff.days > 0:
                return f"{diff.days * 24 + hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        else:
            return "Now"
    except ValueError:
        return reset_time

def draw_limit(win, y, title, fraction, reset_time):
    win.addstr(y, 4, title, curses.A_BOLD)
    y += 1
    
    width = 36
    filled = int(fraction * width)
    bar = "█" * filled + "░" * (width - filled)
    pct_str = f"{fraction*100:.2f}%"
    
    win.addstr(y, 4, "[", curses.color_pair(6))
    win.addstr(y, 5, bar, curses.color_pair(2))
    win.addstr(y, 5 + width, f"] {pct_str}", curses.color_pair(6))
    y += 1
    
    if fraction >= 0.9999:
        win.addstr(y, 4, "Quota available", curses.color_pair(2))
    else:
        reset_str = format_reset_time(reset_time)
        win.addstr(y, 4, f"{int(fraction*100)}% remaining · Refreshes in {reset_str}", curses.color_pair(2))
    
    y += 2
    return y

def draw_group(win, y, group_name, models_text, quota_info):
    win.addstr(y, 0, group_name, curses.A_BOLD)
    y += 1
    win.addstr(y, 2, f"Models within this group: {models_text}", curses.color_pair(6))
    y += 2
    
    fraction = quota_info.get("remainingFraction", 1.0)
    reset_time = quota_info.get("resetTime", "Unknown")

    y = draw_limit(win, y, "Weekly Limit", 1.0, "Unknown")
    y = draw_limit(win, y, "Five Hour Limit", fraction, reset_time)
        
    y += 1
    return y

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    
    if curses.COLORS >= 256:
        curses.init_pair(2, 192, -1) # Pale greenish yellow
        curses.init_pair(6, 245, -1) # Dim gray
    else:
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(6, curses.COLOR_WHITE, -1)
        
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)

    while True:
        data = get_quota()
        stdscr.clear()
        
        max_y, max_x = stdscr.getmaxyx()
        
        title = " 🚀 Antigravity CLI Quota Top "
        title_x = max(0, max_x//2 - len(title)//2)
        stdscr.addstr(0, title_x, title, curses.color_pair(4) | curses.A_BOLD)
        
        if not data:
            stdscr.addstr(2, 2, "Could not connect to agy language server. Is agy running?", curses.color_pair(3))
        else:
            status = data.get("userStatus", {})
            user_tier = status.get("userTier", {}).get("name", "Unknown Tier")
            stdscr.addstr(2, 2, f"Account Tier: {user_tier}", curses.color_pair(5) | curses.A_BOLD)
            
            models = status.get("cascadeModelConfigData", {}).get("clientModelConfigs", [])
            
            gemini_quota = None
            claude_quota = None
            
            for m in models:
                lbl = m.get("label", "")
                if "Gemini" in lbl and not gemini_quota and "quotaInfo" in m:
                    gemini_quota = m["quotaInfo"]
                if ("Claude" in lbl or "GPT" in lbl) and not claude_quota and "quotaInfo" in m:
                    claude_quota = m["quotaInfo"]
                    
            if not gemini_quota: gemini_quota = {"remainingFraction": 1.0, "resetTime": "Unknown"}
            if not claude_quota: claude_quota = {"remainingFraction": 1.0, "resetTime": "Unknown"}
            
            y = 4
            
            y = draw_group(stdscr, y, "GEMINI MODELS", "Gemini Flash, Gemini Pro", gemini_quota)
            y = draw_group(stdscr, y, "CLAUDE AND GPT MODELS", "Claude Opus, Claude Sonnet, GPT-OSS", claude_quota)
                    
        stdscr.addstr(max_y-1, 2, "Press 'q' to quit. Updating every 1 minute...", curses.A_DIM)
        stdscr.refresh()
        
        for _ in range(600):
            try:
                key = stdscr.getkey()
                if key == 'q':
                    return
            except curses.error:
                pass
            time.sleep(0.1)

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
