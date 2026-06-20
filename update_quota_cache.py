#!/usr/bin/env python3
import json
import os
import subprocess
import urllib.request
import urllib.error

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
                    try:
                        port = int(addr_port.split(':')[-1])
                        ports.append(port)
                    except ValueError:
                        pass
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
                        try:
                            port = int(addr.split(':')[-1])
                            ports.append(port)
                        except ValueError:
                            pass
        except Exception:
            pass
    return list(set(ports))

def fetch_quota_data(port):
    url = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
    req = urllib.request.Request(url, data=b"{}", headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
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

if __name__ == '__main__':
    data = get_quota()
    if data:
        cache_path = os.path.expanduser("~/.cache/agy_quota.json")
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        # Write to a temporary file first, then rename to ensure atomic write
        tmp_path = cache_path + ".tmp"
        try:
            with open(tmp_path, "w") as f:
                json.dump(data, f)
            os.rename(tmp_path, cache_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
