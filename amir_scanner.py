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
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import urllib3

# غیرفعال کردن هشدار SSL
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

GITHUB_IP_URL = "https://raw.githubusercontent.com/amir1388hev-glitch/termux_ip/main/Termux_ips"

DOWNLOAD_DIR = "/sdcard/Download"
LOCAL_ALL_IPS_FILE = os.path.join(DOWNLOAD_DIR, "all_ips.txt")
CONFIG_CACHE_FILE = os.path.join(os.path.expanduser("~"), ".amir_config_cache.json")

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
    "workers": 20,
    "test_download": True
}

TLS_PORTS = [443, 8443, 2053, 2083, 2087, 2096]
NON_TLS_PORTS = [80, 8080, 8880, 2052, 2082, 2086, 2095]
PORTS_TO_TEST = TLS_PORTS + NON_TLS_PORTS

stop_scan = False
COUNTRY_CACHE = {}

def load_saved_credentials():
    if os.path.exists(CONFIG_CACHE_FILE):
        try:
            with open(CONFIG_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_credentials(email, api_key):
    try:
        data = {"email": email, "api_key": api_key}
        with open(CONFIG_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def get_ip_country(ip):
    ip_prefix = ".".join(ip.split(".")[:3])
    if ip_prefix in COUNTRY_CACHE:
        return COUNTRY_CACHE[ip_prefix]

    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=country", timeout=3)
        if res.status_code == 200:
            country = res.json().get("country", "Unknown")
            if country and country != "Unknown":
                COUNTRY_CACHE[ip_prefix] = country
                return country
    except Exception:
        pass

    try:
        res = requests.get(f"https://ipmyp.ir/api/ip/{ip}", timeout=3)
        data = res.json()
        country = data.get("country") or data.get("country_name") or "Unknown"
        if country != "Unknown":
            COUNTRY_CACHE[ip_prefix] = country
            return country
    except Exception:
        pass

    return "Unknown"

def split_message_smart(text, max_length=3500):
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for line in lines:
        if current_length + len(line) + 1 > max_length:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = len(line)
        else:
            current_chunk.append(line)
            current_length += len(line) + 1

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

def send_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    chunks = split_message_smart(text, max_length=3800)
    for chunk in chunks:
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "disable_web_page_preview": True}
        try:
            requests.post(url, json=payload, timeout=15)
        except Exception:
            pass

def send_to_rubika(text):
    if not RUBIKA_BOT_TOKEN or not RUBIKA_CHAT_ID:
        return
    url = f"https://botapi.rubika.ir/v01/{RUBIKA_BOT_TOKEN}/sendMessage"
    chunks = split_message_smart(text, max_length=3200)
    for chunk in chunks:
        payload = {"chat_id": RUBIKA_CHAT_ID, "text": chunk}
        try:
            requests.post(url, json=payload, timeout=12)
        except Exception:
            pass

def send_to_bale(text):
    if not BALE_BOT_TOKEN or not BALE_CHAT_ID:
        return
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    chunks = split_message_smart(text, max_length=3800)
    for chunk in chunks:
        payload = {"chat_id": BALE_CHAT_ID, "text": chunk}
        try:
            requests.post(url, json=payload, timeout=15)
        except Exception:
            pass

def send_results_by_country(working_results, title_msg, is_config=False):
    if not working_results:
        return
    country_groups = {}
    for item in working_results:
        if is_config:
            ip, lat, country, cfg_str = item
            val = cfg_str
        else:
            target_str, lat, country = item
            val = target_str

        if country not in country_groups:
            country_groups[country] = []
        country_groups[country].append(val)

    for country, items in country_groups.items():
        lines = [f"📊 {title_msg}\n"] + items + [f"\n🏴 کشور: {country} | تعداد: {len(items)} عدد", f"\n🔥 آی‌پی تمیز خدمت شما:\nآیدی تلگرام سازنده: {TELEGRAM_ID}\nAMIR CONFIG SPEED"]
        single_message = "\n".join(lines)
        send_to_telegram(single_message)
        send_to_rubika(single_message)
        send_to_bale(single_message)
        time.sleep(1)

def get_clean_input(prompt_text):
    try:
        raw_val = input(prompt_text)
        return re.sub(r"\D", "", raw_val)
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)

def get_ips_from_github(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            lines = response.text.splitlines()
            ips = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
            return parse_ip_input(",".join(ips))
    except Exception:
        pass
    return []

def get_ips_from_local_file():
    if os.path.exists(LOCAL_ALL_IPS_FILE):
        try:
            with open(LOCAL_ALL_IPS_FILE, "r", encoding="utf-8") as f:
                raw_ips = [line.strip().split()[0].split(":")[0] for line in f if line.strip() and not line.startswith("#")]
                if raw_ips:
                    return parse_ip_input(",".join(raw_ips))
        except Exception:
            pass
    return []

def parse_ip_input(user_input):
    ips = []
    for entry in user_input.replace("\n", ",").split(","):
        entry = entry.strip()
        if not entry: continue
        if "/" in entry:
            try:
                for ip in ipaddress.ip_network(entry, strict=False).hosts():
                    ips.append(str(ip))
            except Exception: pass
        else:
            try:
                ipaddress.ip_address(entry)
                ips.append(entry)
            except Exception: pass
    return ips

def get_manual_ips():
    print(Colors.CYAN + "\nEnter IPs (Paste list, press ENTER twice when done):\n" + Colors.END)
    lines = []
    while True:
        try:
            line = input().strip()
            if not line:
                if lines: break
                else: return []
            lines.append(line)
        except (KeyboardInterrupt, EOFError): break
    return parse_ip_input(",".join(lines))

def select_ip_source():
    print(Colors.CYAN + "\nSelect IP source:" + Colors.END)
    print("1. GitHub")
    print("2. Manual input")
    print("3. Local file (/sdcard/Download/all_ips.txt)")
    choice = get_clean_input(Colors.BOLD + "[>] Choose (1/2/3): " + Colors.END)
    if choice == "1": return get_ips_from_github(GITHUB_IP_URL)
    elif choice == "2": return get_manual_ips()
    elif choice == "3": return get_ips_from_local_file()
    return []

def check_ip_http_latency(ip, port=443, domain="chatgpt.com", timeout=3.0, test_download=True, path="/"):
    for attempt in range(2):
        start_time = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            if port in NON_TLS_PORTS:
                sock.sendall(f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n".encode())
                res = sock.recv(1024)
                sock.close()
                if not res: continue
            else:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                tls_sock = context.wrap_socket(sock, server_hostname=domain)
                tls_sock.sendall(f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n".encode())
                res = tls_sock.recv(1024)
                tls_sock.close()
                sock.close()
                if not res: continue
            return round((time.time() - start_time) * 1000, 1)
        except Exception:
            if attempt == 1: return None
    return None

def save_to_file(filename_only, data):
    filepath = os.path.join(DOWNLOAD_DIR, filename_only)
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
        print(Colors.GREEN + f"\n[+] Saved to: {filepath}" + Colors.END)
    except Exception:
        pass

def print_banner():
    print(f"""{Colors.CYAN}{Colors.BOLD}
 ╔══════════════════════════════════════════════════════════════════╗
 ║                     AMIR CONFIG SPEED PRO                        ║
 ╠══════════════════════════════════════════════════════════════════╝
 ║  {Colors.YELLOW}► Version        :{Colors.WHITE} v2.2.0 (API Cloudflare Edition) {Colors.CYAN} ║
 ║  {Colors.YELLOW}► Telegram Admin :{Colors.WHITE} {TELEGRAM_ID:<22}{Colors.CYAN}                 ║
 ║  {Colors.YELLOW}► Rubika Admin   :{Colors.WHITE} {RUBIKA_ID:<22}{Colors.CYAN}                 ║
 ╚══════════════════════════════════════════════════════════════════╝
""")

def finalize_and_send(working_results, total_ips, title_msg, save_filename, is_config=False):
    working_results.sort(key=lambda x: x[1])
    clean_data = [item[3] if is_config else item[0] for item in working_results]
    save_to_file(save_filename, "\n".join(clean_data))
    if working_results:
        send_results_by_country(working_results, title_msg, is_config)
    print(Colors.GREEN + f"\n[SUMMARY] Working: {len(working_results)} | Total: {total_ips}" + Colors.END)

def run_scanner_engine(ips, port, domain, timeout, test_download, path, workers):
    global stop_scan
    stop_scan = False
    working_results = []
    import threading
    lock = threading.Lock()

    def worker_task(ip):
        if stop_scan: return
        lat = check_ip_http_latency(ip, port=port, domain=domain, timeout=timeout, test_download=test_download, path=path)
        if lat is not None:
            country = get_ip_country(ip)
            with lock:
                working_results.append((ip, lat, country))
                print(f"{ip:<18} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}")
        else:
            print(f"{ip:<18} | {Colors.RED}[DEAD]{Colors.END}")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = [executor.submit(worker_task, ip) for ip in ips]
            for f in as_completed(futures):
                if stop_scan: break
        except KeyboardInterrupt:
            stop_scan = True

    return working_results, len(ips)

def menu_option_1():
    ips = select_ip_source()
    if not ips: return
    res, total = run_scanner_engine(ips, SCAN_SETTINGS['port'], SCAN_SETTINGS['domain'], SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], SCAN_SETTINGS['path'], SCAN_SETTINGS['workers'])
    finalize_and_send(res, total, "Clean IPs", "IP_Health_Check.txt")

def menu_option_8_cloudflare_api_deploy():
    os.system("clear")
    print(f"""{Colors.CYAN}{Colors.BOLD}
 ╔══════════════════════════════════════════════════════════════════╗
 ║                       AMIR CONFIG SPEED                          ║
 ║                 Telegram: {TELEGRAM_ID:<33} ║
 ╚══════════════════════════════════════════════════════════════════╝
{Colors.END}""")
    print(Colors.YELLOW + "\n[>] Option 8: Cloudflare API Auto Deploy & Web-View Sub Generator" + Colors.END)
    
    saved = load_saved_credentials()
    email, api_key = "", ""
    
    if saved and "email" in saved and "api_key" in saved:
        print(Colors.GREEN + f"\n[+] Found saved credentials for: {saved['email']}" + Colors.END)
        choice = input(Colors.BOLD + "Do you want to use saved credentials? (Y/n): " + Colors.END).strip().lower()
        if choice != 'n':
            email = saved["email"]
            api_key = saved["api_key"]
    
    if not email or not api_key:
        email = input(Colors.BOLD + "Enter your Cloudflare Account Email: " + Colors.END).strip()
        api_key = input(Colors.BOLD + "Enter your Cloudflare Global API Key / Token: " + Colors.END).strip()
        if email and api_key:
            save_credentials(email, api_key)

    if not email or not api_key:
        print(Colors.RED + "[!] Email and API Key are required!" + Colors.END)
        return

    print(Colors.BLUE + "\n[*] Verifying Cloudflare API credentials..." + Colors.END)
    headers = {"X-Auth-Email": email, "X-Auth-Key": api_key, "Content-Type": "application/json"}
    
    try:
        verify_res = requests.get("https://api.cloudflare.com/client/v4/user", headers=headers, timeout=10).json()
        if not verify_res.get("success"):
            print(Colors.RED + "[✕] Invalid credentials! Please check your email or API Key." + Colors.END)
            return
        
        acc_res = requests.get("https://api.cloudflare.com/client/v4/accounts", headers=headers, timeout=10).json()
        account_id = acc_res["result"][0]["id"]
    except Exception as e:
        print(Colors.RED + f"[!] Connection error: {e}" + Colors.END)
        return

    username = input(Colors.BOLD + "Enter Username (Name): " + Colors.END).strip() or "AmirUser"
    traffic_limit = input(Colors.BOLD + "Enter Traffic Limit (e.g. 100 GB): " + Colors.END).strip() or "Unlimited"
    duration = input(Colors.BOLD + "Enter Duration (e.g. 30 Days): " + Colors.END).strip() or "30 Days"

    print(Colors.BLUE + "\n[*] Deploying Worker and JavaScript script to Cloudflare..." + Colors.END)

    worker_name = f"amir-config-speed-{int(time.time())}"
    sub_link = f"https://{worker_name}.workers.dev/sub/{username}"

    worker_js_code = f"""
export default {{
  async fetch(request, env, ctx) {{
    const html = `<!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AMIR CONFIG SPEED - Subscriptions</title>
        <style>
            body {{ background-color: #0b0f19; color: #ffffff; font-family: Tahoma, sans-serif; text-align: center; padding: 20px; }}
            .card {{ background: #131b2e; border: 1px solid #1f293d; border-radius: 15px; padding: 20px; max-width: 400px; margin: auto; box-shadow: 0 0 20px rgba(0,255,255,0.1); }}
            .status {{ color: #00ffcc; font-weight: bold; margin-bottom: 15px; }}
            .btn {{ background: #ffcc00; color: #000; padding: 10px 20px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 15px; width: 100%; text-decoration: display; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>⚡ AMIR CONFIG SPEED ⚡</h2>
            <p class="status">وضعیت: فعال و متصل (Active)</p>
            <p>نام کاربری: <b>{username}</b></p>
            <p>حجم مصرفی: <b>{traffic_limit}</b></p>
            <p>مدت اعتبار: <b>{duration}</b></p>
            <hr style="border:0; border-top:1px solid #222; margin:15px 0;">
            <p style="font-size: 13px; color: #aaa;">سازنده: {TELEGRAM_ID}</p>
            <a href="vless://..." class="btn">کپی لینک سابسکریپشن</a>
        </div>
    </body>
    </html>`;
    return new Response(html, {{ headers: {{ "content-type": "text/html;charset=UTF-8" }} }});
  }}
}};
"""

    deploy_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{worker_name}"
    deploy_headers = {"X-Auth-Email": email, "X-Auth-Key": api_key, "Content-Type": "application/javascript"}
    
    try:
        dep_res = requests.put(deploy_url, headers=deploy_headers, data=worker_js_code, timeout=15).json()
        if dep_res.get("success"):
            print(Colors.GREEN + "[✓] Worker and JavaScript code successfully deployed!" + Colors.END)
        else:
            print(Colors.YELLOW + "[!] Worker created, but check API response manually." + Colors.END)
    except Exception as e:
        print(Colors.RED + f"[!] Deployment warning: {e}" + Colors.END)

    print(Colors.CYAN + f"\n[🔗] Final Working Subscription Link:\n{sub_link}" + Colors.END)

    report_text = f"""🚀 پنل سابسکریپشن کهکشانی AMIR CONFIG SPEED با موفقیت دیپلوی شد!

👤 نام کاربری: {username}
👑 سازنده: AMIR CONFIG SPEED
💬 آیدی تلگرام: {TELEGRAM_ID}

-----------------------------------
📊 حجم اشتراک: {traffic_limit}
⏳ مدت زمان: {duration}

🔗 لینک سابسکریپشن اختصاصی:
{sub_link}
"""
    send_to_telegram(report_text)
    send_to_rubika(report_text)
    send_to_bale(report_text)
    print(Colors.GREEN + "[+] Report sent to all messengers!" + Colors.END)

def main_menu():
    while True:
        print_banner()
        print(f"""{Colors.CYAN}
 ╔══════════════════════════════════════════════════════════════════╗
 ║  {Colors.GREEN}[1] Test IP Health{Colors.CYAN}                                              ║
 ║  {Colors.MAGENTA}[8] AMIR CONFIG SPEED - Cosmic Web-View Sub (Auto Deploy){Colors.CYAN}      ║
 ║  {Colors.END}{Colors.CYAN}[0] Exit{Colors.CYAN}                                                       ║
 ╚══════════════════════════════════════════════════════════════════╝
""")
        choice = get_clean_input(Colors.BOLD + "[>] Select option: " + Colors.END)
        if choice == "1": menu_option_1()
        elif choice == "8": menu_option_8_cloudflare_api_deploy()
        elif choice == "0": sys.exit(0)
        input(Colors.BOLD + "\n[*] Press Enter to continue..." + Colors.END)
        os.system("clear")

if __name__ == "__main__":
    main_menu()
