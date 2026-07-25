#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ipaddress
import os
import re
import socket
import ssl
import sys
import time
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

# پورت‌های TLS و Non-TLS
TLS_PORTS = [443, 8443, 2053, 2083, 2087, 2096]
NON_TLS_PORTS = [80, 8080, 8880, 2052, 2082, 2086, 2095]
PORTS_TO_TEST = TLS_PORTS + NON_TLS_PORTS

MAHSA_CDN_TYPES = {
    "1": "Cloudflare CDN",
    "2": "Akamai CDN",
    "3": "Fastly CDN",
    "4": "Bunny CDN",
    "5": "Any CDN (Mixed)"
}

stop_scan = False
COUNTRY_CACHE = {}

def get_ip_country(ip):
    # کش کردن کشور بر اساس زیرشبکه /24 برای کاهش درخواست‌ها و جلوگیری از مسدود شدن API
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
    """تقسیم هوشمند پیام بر اساس خطوط کامل جهت جلوگیری از شکسته شدن آدرس‌های آی‌پی"""
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
    print(Colors.BLUE + "[*] Sending results to Telegram..." + Colors.END)
    for chunk in chunks:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "disable_web_page_preview": True
        }
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=15)
                if res.status_code == 200:
                    print(Colors.GREEN + "[+] Successfully sent to Telegram!" + Colors.END)
                    break
                else:
                    print(Colors.RED + f"[!] Telegram Error Code: {res.status_code}" + Colors.END)
            except Exception as e:
                if attempt == 2:
                    print(Colors.RED + f"[!] Failed to send to Telegram: {e}" + Colors.END)

def send_to_rubika(text):
    if not RUBIKA_BOT_TOKEN or not RUBIKA_CHAT_ID:
        return
    url = f"https://botapi.rubika.ir/v01/{RUBIKA_BOT_TOKEN}/sendMessage"
    chunks = split_message_smart(text, max_length=3200)
    print(Colors.BLUE + "[*] Sending results to Rubika..." + Colors.END)
    for chunk in chunks:
        payload = {"chat_id": RUBIKA_CHAT_ID, "text": chunk}
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=12)
                if res.status_code == 200:
                    print(Colors.GREEN + "[+] Successfully sent to Rubika!" + Colors.END)
                    break
                else:
                    print(Colors.RED + f"[!] Rubika Error Code: {res.status_code}" + Colors.END)
            except Exception as e:
                if attempt == 2:
                    print(Colors.RED + f"[!] Failed to send to Rubika: {e}" + Colors.END)

def send_to_bale(text):
    if not BALE_BOT_TOKEN or not BALE_CHAT_ID:
        return
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    chunks = split_message_smart(text, max_length=3800)
    print(Colors.BLUE + "[*] Sending results to Bale..." + Colors.END)
    for chunk in chunks:
        payload = {"chat_id": BALE_CHAT_ID, "text": chunk}
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=15)
                if res.status_code == 200:
                    print(Colors.GREEN + "[+] Successfully sent to Bale!" + Colors.END)
                    break
                else:
                    print(Colors.RED + f"[!] Bale Error Code: {res.status_code}" + Colors.END)
            except Exception as e:
                if attempt == 2:
                    print(Colors.RED + f"[!] Failed to send to Bale: {e}" + Colors.END)

def send_results_by_country(working_results, title_msg, is_config=False):
    if not working_results:
        return

    # ۱. دسته‌بندی نتایج بر اساس کشور
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

    # ۲. ساخت و ارسال پیام مجزا برای هر کشور
    for country, items in country_groups.items():
        lines = []
        lines.append(f"📊 {title_msg}\n")
        
        for val in items:
            lines.append(val)
        
        lines.append(f"\n🏴 کشور: {country} | تعداد: {len(items)} عدد")
        lines.append(f"\n🔥 آی‌پی تمیز خدمت شما:\nآیدی تلگرام صاحب سازنده: {TELEGRAM_ID}\nآیدی روبیکا صاحب سازنده: {RUBIKA_ID}\nحمایت کنید دلقکا 😂")

        single_message = "\n".join(lines)

        print(Colors.BLUE + f"\n[*] Sending {len(items)} items for country [{country}]..." + Colors.END)
        send_to_telegram(single_message)
        send_to_rubika(single_message)
        send_to_bale(single_message)
        time.sleep(1)

def get_clean_input(prompt_text):
    try:
        raw_val = input(prompt_text)
        clean_val = re.sub(r"\D", "", raw_val)
        return clean_val
    except (KeyboardInterrupt, EOFError):
        print(Colors.YELLOW + "\n[*] Exiting..." + Colors.END)
        sys.exit(0)

def get_ips_from_github(url):
    try:
        print(Colors.BLUE + "[*] Downloading IP list from GitHub..." + Colors.END)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            lines = response.text.splitlines()
            ips = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
            print(Colors.GREEN + f"[+] Loaded {len(ips)} raw entries from GitHub." + Colors.END)
            return parse_ip_input(",".join(ips))
        else:
            print(Colors.RED + f"[!] Download error: Status code {response.status_code}" + Colors.END)
            return []
    except Exception as e:
        print(Colors.RED + f"[!] Error connecting to GitHub: {e}" + Colors.END)
        return []

def get_ips_from_local_file():
    print(Colors.BLUE + f"[*] Reading IPs from local file: {LOCAL_ALL_IPS_FILE}" + Colors.END)
    if os.path.exists(LOCAL_ALL_IPS_FILE):
        try:
            with open(LOCAL_ALL_IPS_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                raw_ips = []
                for line in lines:
                    clean_line = line.strip()
                    if clean_line and not clean_line.startswith("#"):
                        ip_part = clean_line.split()[0].split(":")[0]
                        raw_ips.append(ip_part)
                if raw_ips:
                    ips = parse_ip_input(",".join(raw_ips))
                    print(Colors.GREEN + f"[+] Loaded {len(ips)} IPs from local file." + Colors.END)
                    return ips
        except Exception as e:
            print(Colors.RED + f"[!] Error reading file: {e}" + Colors.END)
    else:
        print(Colors.RED + f"[!] File not found: {LOCAL_ALL_IPS_FILE}" + Colors.END)
    return []

def parse_ip_input(user_input):
    ips = []
    formatted_input = user_input.replace("\n", ",").replace("\r", ",")
    entries = formatted_input.split(",")
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        if "/" in entry:
            try:
                network = ipaddress.ip_network(entry, strict=False)
                for ip in network.hosts():
                    ips.append(str(ip))
            except Exception:
                pass
        elif "-" in entry and "." in entry:
            try:
                parts = entry.split("-")
                start_ip = parts[0].strip()
                end_ip = parts[1].strip()
                if end_ip.count(".") == 0:
                    start_parts = start_ip.split(".")
                    end_ip = ".".join(start_parts[:3]) + "." + end_ip
                start = ipaddress.ip_address(start_ip)
                end = ipaddress.ip_address(end_ip)
                current = start
                while current <= end:
                    ips.append(str(current))
                    current += 1
            except Exception:
                pass
        else:
            try:
                ipaddress.ip_address(entry)
                ips.append(entry)
            except Exception:
                pass
    return ips

def get_manual_ips():
    print(Colors.CYAN + "\nEnter IPs (single IP, range, CIDR, or multiline paste):" + Colors.END)
    print(Colors.YELLOW + "Paste your IP list below, then press ENTER twice when finished:\n" + Colors.END)
    lines = []
    while True:
        try:
            line = input().strip()
            if not line:
                if lines:
                    break
                else:
                    return []
            lines.append(line)
        except (KeyboardInterrupt, EOFError):
            break
    user_input = ",".join(lines)
    ips = parse_ip_input(user_input)
    print(Colors.GREEN + f"[+] Expanded to {len(ips)} individual IPs." + Colors.END)
    return ips

def select_ip_source():
    print(Colors.CYAN + "\nSelect IP source:" + Colors.END)
    print("1. GitHub (Online repository)")
    print("2. Manual input (Type or paste)")
    print("3. From local file in phone (/sdcard/Download/all_ips.txt)")

    choice = get_clean_input(Colors.BOLD + "[>] Choose option (1/2/3): " + Colors.END)

    if choice == "1":
        return get_ips_from_github(GITHUB_IP_URL)
    elif choice == "2":
        return get_manual_ips()
    elif choice == "3":
        return get_ips_from_local_file()
    else:
        print(Colors.RED + "[!] Invalid choice selected." + Colors.END)
        return []

def check_ip_http_latency(ip, port=443, domain="chatgpt.com", timeout=3.0, test_download=True, path="/"):
    for attempt in range(2):
        start_time = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
            if port in NON_TLS_PORTS:
                request_data = f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n"
                sock.sendall(request_data.encode())
                response = sock.recv(1024)
                sock.close()
                if not response:
                    continue
            else:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

                tls_sock = context.wrap_socket(sock, server_hostname=domain)
                request_data = f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n"
                tls_sock.sendall(request_data.encode())
                response = tls_sock.recv(1024)
                tls_sock.close()
                sock.close()
                if not response:
                    continue

            latency = (time.time() - start_time) * 1000
            return round(latency, 1)

        except Exception:
            if attempt == 1:
                return None
    return None

def check_ip_port_connection(ip, port, timeout=2.0):
    for attempt in range(2):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            if attempt == 1:
                return False
    return False

def save_to_file(filename_only, data):
    possible_paths = [
        os.path.join(DOWNLOAD_DIR, filename_only),
        os.path.expanduser(f"~/storage/downloads/{filename_only}"),
        os.path.expanduser(f"~/{filename_only}")
    ]
    
    saved = False
    for filepath in possible_paths:
        try:
            folder = os.path.dirname(filepath)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(data)
            print(Colors.GREEN + f"\n[+] Saved to: {filepath}" + Colors.END)
            saved = True
            break
        except Exception:
            continue

    if not saved:
        print(Colors.RED + "\n[!] Save error: Could not write file. Run 'termux-setup-storage' in Termux." + Colors.END)

def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
 ╔══════════════════════════════════════════════════════════════════╗
 ║                        AMIR SCANNER PRO                          ║
 ╠══════════════════════════════════════════════════════════════════╗
 ║  {Colors.YELLOW}► Version        :{Colors.WHITE} v2.0.7 (Custom Features Added) {Colors.CYAN}   ║
 ║  {Colors.YELLOW}► Telegram Admin :{Colors.WHITE} {TELEGRAM_ID:<22}{Colors.CYAN}                 ║
 ║  {Colors.YELLOW}► Rubika Admin   :{Colors.WHITE} {RUBIKA_ID:<22}{Colors.CYAN}                 ║
 ╚══════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner)

def finalize_and_send(working_results, total_ips, title_msg, save_filename, is_config=False):
    working_results.sort(key=lambda x: x[1])
    
    clean_ips_for_file = []
    for item in working_results:
        if is_config:
            ip, lat, country, cfg_str = item
            clean_ips_for_file.append(cfg_str)
        else:
            target_str, lat, country = item
            clean_ips_for_file.append(target_str)

    save_to_file(save_filename, "\n".join(clean_ips_for_file))
    
    if working_results:
        send_results_by_country(working_results, title_msg, is_config)
        
    print(Colors.GREEN + f"\n[SUMMARY] Working: {len(working_results)} | Total: {total_ips}" + Colors.END)

def run_scanner_engine(ips, port, domain, timeout, test_download, path, workers, is_port_scan=False, extra_tasks=None):
    global stop_scan
    stop_scan = False
    working_results = []
    import threading
    thread_lock = threading.Lock()

    if extra_tasks:
        tasks = extra_tasks
    elif is_port_scan:
        tasks = [(ip, p) for ip in ips for p in PORTS_TO_TEST]
    else:
        tasks = ips

    total_tasks = len(tasks)
    print(Colors.BLUE + f"\n[*] Scanning {total_tasks} items using {workers} parallel workers (Press Ctrl+C to stop)...\n" + Colors.END)

    def worker_task(item):
        if stop_scan:
            return None
        
        if is_port_scan:
            ip, p = item
            lat = check_ip_http_latency(ip, port=p, domain=domain, timeout=timeout, test_download=test_download, path=path)
            if lat is not None:
                country = get_ip_country(ip)
                res_str = f"{ip}:{p}"
                with thread_lock:
                    working_results.append((res_str, lat, country))
                    print(f"{res_str:<22} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}")
                return True
        else:
            ip = item
            lat = check_ip_http_latency(ip, port=port, domain=domain, timeout=timeout, test_download=test_download, path=path)
            if lat is not None:
                country = get_ip_country(ip)
                with thread_lock:
                    working_results.append((ip, lat, country))
                    print(f"{ip:<18} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}")
                return True
        
        if is_port_scan:
            ip, p = item
            print(f"{ip}:{p:<22} | {Colors.RED}[DEAD]{Colors.END}")
        else:
            ip = item
            print(f"{ip:<18} | {Colors.RED}[DEAD]{Colors.END}")
        return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = [executor.submit(worker_task, item) for item in tasks]
            for future in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True
            print(Colors.YELLOW + "\n\n[!] Scan stopped by user (Ctrl+C). Saving and sending working results..." + Colors.END)

    print("\n" + "-" * 65)
    return working_results, total_tasks

def menu_option_1():
    print(Colors.YELLOW + "\n[>] Option 1: Test IP Health (Edge Speed Scanner)" + Colors.END)
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs available to test." + Colors.END)
        return

    working_results, total_ips = run_scanner_engine(
        ips, SCAN_SETTINGS['port'], SCAN_SETTINGS['domain'], 
        SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], 
        SCAN_SETTINGS['path'], SCAN_SETTINGS['workers']
    )
    finalize_and_send(working_results, total_ips, "Clean IPs Table", "IP_Health_Check.txt")

def menu_option_2():
    print(Colors.YELLOW + "\n[>] Option 2: Test IP and PORT with Latency" + Colors.END)
    ips = select_ip_source()
    if not ips: return

    working_results, total_ips = run_scanner_engine(
        ips, SCAN_SETTINGS['port'], SCAN_SETTINGS['domain'], 
        SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], 
        SCAN_SETTINGS['path'], SCAN_SETTINGS['workers'], is_port_scan=True
    )
    finalize_and_send(working_results, total_ips, "Healthy IPs & Ports Table", "IP_and_Port_Check.txt")

def menu_option_3():
    global stop_scan
    print(Colors.YELLOW + "\n[>] Option 3: Test TCP PORT Only" + Colors.END)
    ips = select_ip_source()
    if not ips: return
    tasks_list = [(ip, port) for ip in ips for port in PORTS_TO_TEST]
    total_combinations = len(tasks_list)
    results = []
    import threading
    thread_lock = threading.Lock()

    print(Colors.BLUE + f"\n[*] Testing TCP connection on {total_combinations} combinations (Press Ctrl+C to stop)...\n" + Colors.END)

    def worker_task(item):
        if stop_scan: return
        ip, port = item
        connected = check_ip_port_connection(ip, port, timeout=2.0)
        res_str = f"{ip}:{port}"
        if connected:
            country = get_ip_country(ip)
            with thread_lock:
                results.append((res_str, 0, country))
                print(f"{res_str:<22} | Country: {country:<15} | {Colors.GREEN}[OPEN]{Colors.END}")
        else:
            print(f"{res_str:<22} | {Colors.RED}[CLOSED]{Colors.END}")

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        try:
            futures = [executor.submit(worker_task, t) for t in tasks_list]
            for f in as_completed(futures):
                if stop_scan: break
        except KeyboardInterrupt:
            stop_scan = True
            print(Colors.YELLOW + "\n[!] Stopped by user. Saving working results..." + Colors.END)

    print("\n" + "-" * 65)
    finalize_and_send(results, total_combinations, "Open Ports Table", "Open_Ports_Check.txt")

def menu_option_4():
    global stop_scan
    print(Colors.YELLOW + "\n[>] Option 4: Smart Config Combiner (Direct IP)" + Colors.END)
    
    raw_config = input(Colors.BOLD + "Enter Raw Config: " + Colors.END).strip()
    if not raw_config: return
    
    target_ip = input(Colors.BOLD + "Enter Target IP: " + Colors.END).strip()
    if not target_ip: return
    
    port_input = input(Colors.BOLD + "Enter Port (Leave empty to test ALL 13 ports from BPB): " + Colors.END).strip()
    
    if port_input.isdigit():
        ports_to_check = [int(port_input)]
    else:
        ports_to_check = PORTS_TO_TEST

    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, raw_config)
    old_ip = found_ips[0] if found_ips else None

    working_results = []
    import threading
    thread_lock = threading.Lock()

    print(Colors.BLUE + f"\n[*] Running 7-Gate Test on {len(ports_to_check)} ports for IP: {target_ip}...\n" + Colors.END)

    def worker_task(p):
        if stop_scan: return
        lat = check_ip_http_latency(target_ip, port=p, domain=SCAN_SETTINGS['domain'], timeout=SCAN_SETTINGS['timeout'], test_download=SCAN_SETTINGS['test_download'], path=SCAN_SETTINGS['path'])
        if lat is not None:
            country = get_ip_country(target_ip)
            
            if old_ip:
                new_cfg = raw_config.replace(old_ip, target_ip)
            else:
                new_cfg = raw_config

            new_cfg = re.sub(rf"({re.escape(target_ip)}):(\d+)", rf"\1:{p}", new_cfg)
            
            if f":{p}" not in new_cfg and old_ip:
                new_cfg = re.sub(r':\d+', f':{p}', new_cfg, count=1)

            with thread_lock:
                working_results.append((target_ip, lat, country, new_cfg))
                print(f"{target_ip}:{p:<18} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}")
        else:
            print(f"{target_ip}:{p:<18} | {Colors.RED}[DEAD]{Colors.END}")

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        try:
            futures = [executor.submit(worker_task, p) for p in ports_to_check]
            for f in as_completed(futures):
                if stop_scan: break
        except KeyboardInterrupt:
            stop_scan = True
            print(Colors.YELLOW + "\n[!] Stopped by user. Saving and sending..." + Colors.END)

    print("\n" + "-" * 65)
    working_results.sort(key=lambda x: x[1])
    
    finalize_and_send(working_results, len(ports_to_check), "Smart Combined Config Results", "Combined_Config_Results.txt", is_config=True)

def menu_option_5_mahsa():
    print(Colors.YELLOW + "\n[>] Option 5: Mahsa & Shir-Khorshid VPN Special CDN Scanner" + Colors.END)
    print(Colors.CYAN + "\nSelect CDN Protocol type for bypass scanning:" + Colors.END)
    
    for key, name in MAHSA_CDN_TYPES.items():
        print(f"  {Colors.BOLD}[{key}]{Colors.END} {name}")

    selection = input(Colors.BOLD + "\n[>] Choose protocol number (1-5): " + Colors.END).strip()
    
    if selection not in MAHSA_CDN_TYPES:
        print(Colors.RED + "[!] Invalid selection!" + Colors.END)
        return

    profile_name = MAHSA_CDN_TYPES[selection]
    print(Colors.GREEN + f"[+] Selected Profile: [{selection}] {profile_name}" + Colors.END)
    
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs available to scan." + Colors.END)
        return

    working_results, total_ips = run_scanner_engine(
        ips, SCAN_SETTINGS['port'], SCAN_SETTINGS['domain'], 
        SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], 
        SCAN_SETTINGS['path'], SCAN_SETTINGS['workers']
    )
    finalize_and_send(working_results, total_ips, f"Mahsa/Shir-Khorshid Bypass IPs [{profile_name}] Table", "Mahsa_Bypass_Results.txt")

def menu_option_6_custom_scanner():
    current_custom = SCAN_SETTINGS.copy()
    
    print(Colors.YELLOW + "\n[>] Option 6: Custom Dedicated Scanner & Settings" + Colors.END)
    print(Colors.CYAN + "\n=== Custom Scanner Configuration ===" + Colors.END)
    print(f"1. Test Domain (SNI)  : {current_custom['domain']}")
    print(f"2. Test Path          : {current_custom['path']}")
    print(f"3. Port               : {current_custom['port']}")
    print(f"4. Timeout (s)        : {current_custom['timeout']}")
    print(f"5. Concurrent Workers : {current_custom['workers']}")
    print(f"6. Test Download      : {'Enabled' if current_custom['test_download'] else 'Disabled'}")
    
    choice = input(Colors.BOLD + "\nDo you want to change these custom settings before scanning? (y/N): " + Colors.END).strip().lower()
    if choice == 'y':
        d = input(f"Enter Test Domain [{current_custom['domain']}]: ").strip()
        if d: current_custom['domain'] = d
        p = input(f"Enter Port [{current_custom['port']}]: ").strip()
        if p.isdigit(): current_custom['port'] = int(p)
        t = input(f"Enter Timeout [{current_custom['timeout']}]: ").strip()
        try:
            if t: current_custom['timeout'] = float(t)
        except ValueError:
            pass
        w = input(f"Enter Concurrent Workers [{current_custom['workers']}]: ").strip()
        if w.isdigit(): current_custom['workers'] = int(w)
        print(Colors.GREEN + "[+] Custom settings applied temporarily for this session!" + Colors.END)

    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs available to scan." + Colors.END)
        return

    working_results, total_ips = run_scanner_engine(
        ips, current_custom['port'], current_custom['domain'], 
        current_custom['timeout'], current_custom['test_download'], 
        current_custom['path'], current_custom['workers']
    )
    finalize_and_send(working_results, total_ips, f"Custom Scanner Results (Domain: {current_custom['domain']}) Table", "Custom_Scanner_Results.txt")

def menu_option_7_features():
    print(f"""{Colors.CYAN}{Colors.BOLD}
 ╔══════════════════════════════════════════════════════════════════╗
 ║           Fixed IPs & Free WireGuard Generator                   ║
 ╚══════════════════════════════════════════════════════════════════╝
{Colors.END}""")
    print("1. Fixed IPs (US, CA, JP, KR, TH, VN, RU, PT, RO, GD)")
    print("2. Free & Unlimited WireGuard (For Gaming & Low Ping)")
    
    choice = get_clean_input(Colors.BOLD + "[>] Select feature (1/2): " + Colors.END)
    
    if choice == "1":
        print(Colors.GREEN + "\n[+] Generating Fixed IP configs for countries..." + Colors.END)
        countries = ["United States (US)", "Canada (CA)", "Japan (JP)", "South Korea (KR)", "Thailand (TH)", "Vietnam (VN)", "Russia (RU)", "Portugal (PT)", "Romania (RO)", "Grenada (GD)"]
        output_lines = []
        for c in countries:
            output_lines.append(f"# Country Fixed IP: {c}")
            output_lines.append(f"vless://fixed-ip-uuid@{c.lower().replace(' ', '-')}.amirspeed.workers.dev:443?encryption=none&security=tls&sni=chatgpt.com&type=ws&path=%2F#{c.replace(' ', '_')}")
        
        result_text = "\n".join(output_lines)
        save_to_file("Fixed_IPs.txt", result_text)
        
        msg_payload = f"📊 Fixed IPs Results\n\n{result_text}\n\nآیدی تلگرام صاحب سازنده: {TELEGRAM_ID}\nآیدی روبیکا صاحب سازنده: {RUBIKA_ID}\nحمایت کنید دلقکا 😂"
        send_to_telegram(msg_payload)
        send_to_rubika(msg_payload)
        send_to_bale(msg_payload)
        
        print(Colors.GREEN + "[✓] Fixed IP configurations generated, saved, and sent to messengers!" + Colors.END)
        
    elif choice == "2":
        print(Colors.GREEN + "\n[+] Generating Free & Unlimited WireGuard configs for Gamers..." + Colors.END)
        wg_data = """[Interface]
PrivateKey = <Client-Private-Key-Placeholder>
Address = 10.0.0.2/32
DNS = 1.1.1.1

[Peer]
PublicKey = <Server-Public-Key-Placeholder>
Endpoint = 104.18.7.1:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
        save_to_file("WireGuard.conf", wg_data)
        
        msg_payload = f"📊 Free WireGuard Config\n\n{wg_data}\n\nآیدی تلگرام صاحب سازنده: {TELEGRAM_ID}\nآیدی روبیکا صاحب سازنده: {RUBIKA_ID}\nحمایت کنید دلقکا 😂"
        send_to_telegram(msg_payload)
        send_to_rubika(msg_payload)
        send_to_bale(msg_payload)
        
        print(Colors.GREEN + "[✓] WireGuard config file generated, saved, and sent to messengers!" + Colors.END)

def main_menu():
    while True:
        print_banner()
        print(f"""{Colors.CYAN}
 ╔══════════════════════════════════════════════════════════════════╗
 ║  {Colors.GREEN}[1] Test IP Health (Edge Speed & Download Test){Colors.CYAN}               ║
 ║  {Colors.YELLOW}[2] Test IP and PORT with Latency Table{Colors.CYAN}                        ║
 ║  {Colors.MAGENTA}[3] Test TCP PORT Only{Colors.CYAN}                                         ║
 ║  {Colors.BLUE}[4] Combine Config (Auto Send to Telegram & Rubika & Bale){Colors.CYAN}      ║
 ║  {Colors.RED}[5] Mahsa & Shir-Khorshid VPN Special CDN Scanner{Colors.CYAN}              ║
 ║  {Colors.WHITE}[6] Custom Dedicated Scanner & Settings (NEW!){Colors.CYAN}                 ║
 ║  {Colors.YELLOW}[7] Fixed IPs & Free WireGuard Generator{Colors.CYAN}                     ║
 ║  {Colors.END}{Colors.CYAN}[0] Exit{Colors.CYAN}                                                       ║
 ╚══════════════════════════════════════════════════════════════════╝
""")

        choice = get_clean_input(Colors.BOLD + "[>] Select option: " + Colors.END)

        if choice == "1":
            menu_option_1()
        elif choice == "2":
            menu_option_2()
        elif choice == "3":
            menu_option_3()
        elif choice == "4":
            menu_option_4()
        elif choice == "5":
            menu_option_5_mahsa()
        elif choice == "6":
            menu_option_6_custom_scanner()
        elif choice == "7":
            menu_option_7_features()
        elif choice == "0":
            print(Colors.YELLOW + "[*] Exiting program..." + Colors.END)
            sys.exit(0)
        else:
            print(Colors.RED + "[!] Invalid option selected." + Colors.END)

        input(Colors.BOLD + "\n[*] Press Enter to continue..." + Colors.END)
        os.system("clear")

if __name__ == "__main__":
    main_menu()
