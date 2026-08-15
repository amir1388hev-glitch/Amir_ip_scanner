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

SCAN_SETTINGS = {
    "domain": "speed.cloudflare.com",
    "path": "/",
    "port": 443,
    "timeout": 1.7,
    "workers": 20,
}

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

def send_to_all_messengers(text):
    t_ok = send_to_telegram(text)
    r_ok = send_to_rubika(text)
    b_ok = send_to_bale(text)
    i_ok = send_to_igap(text)
    return t_ok or r_ok or b_ok or i_ok

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
        else:
            try:
                ipaddress.ip_address(token)
                ips.append(token)
            except Exception:
                pass
    return list(dict.fromkeys(ips))

def get_manual_ips():
    print(Colors.CYAN + "\nEnter IPs (Paste list, press Enter twice to finish):" + Colors.END, flush=True)
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

def configure_scanner_settings():
    global SCAN_SETTINGS
    # مقادیر پیش‌فرض درخواستی شما
    SCAN_SETTINGS["domain"] = "speed.cloudflare.com"
    SCAN_SETTINGS["workers"] = 20
    SCAN_SETTINGS["timeout"] = 1.7
    SCAN_SETTINGS["port"] = 443

    print(Colors.CYAN + "\n--- Scanner Configuration ---" + Colors.END, flush=True)
    try:
        domain_input = input(Colors.BOLD + f"Enter SNI / Domain [Default: {SCAN_SETTINGS['domain']}]: " + Colors.END).strip()
        if domain_input:
            SCAN_SETTINGS["domain"] = domain_input
            
        port_input = input(Colors.BOLD + f"Enter Port [Default: {SCAN_SETTINGS['port']}]: " + Colors.END).strip()
        if port_input.isdigit():
            SCAN_SETTINGS["port"] = int(port_input)

        workers_input = input(Colors.BOLD + f"Enter Workers / Threads [Default: {SCAN_SETTINGS['workers']}]: " + Colors.END).strip()
        if workers_input.isdigit():
            SCAN_SETTINGS["workers"] = int(workers_input)
        
        timeout_input = input(Colors.BOLD + f"Enter Timeout (seconds) [Default: {SCAN_SETTINGS['timeout']}]: " + Colors.END).strip()
        if timeout_input:
            try:
                SCAN_SETTINGS["timeout"] = float(timeout_input)
            except ValueError:
                pass
    except Exception:
        pass

def check_ip_mahsang_fronting(ip, port=443, domain="speed.cloudflare.com", timeout=1.7, path="/"):
    for attempt in range(2):
        start_time = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            tls_sock = context.wrap_socket(sock, server_hostname=domain)
            tls_sock.settimeout(timeout)
            
            fronting_payload = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"User-Agent: Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36\r\n"
                f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
                f"Connection: close\r\n\r\n"
            )
            tls_sock.sendall(fronting_payload.encode())
            response = tls_sock.recv(1024)
            tls_sock.close()
            sock.close()
            
            if response and (b"HTTP" in response or b"Cloudflare" in response or len(response) > 0):
                latency = (time.time() - start_time) * 1000
                return round(latency, 1)
        except Exception:
            if attempt == 1:
                return None
    return None

def save_to_file(filename_only, data):
    filepath = os.path.join(DOWNLOAD_DIR, filename_only)
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
    except Exception:
        pass

def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════╗
║ AMIR SCANNER PRO - MAHSANG & XRAY ENGINE                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║ {Colors.YELLOW}► Version :{Colors.WHITE} v3.0.0 (Custom Terminal & Messenger Mode){Colors.CYAN}           ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner, flush=True)

def finalize_and_send(working_results, dead_count, header_prefix, port_tested, save_filename, is_config=False):
    working_results.sort(key=lambda x: x[1])
    clean_ips_for_file = []
    telegram_lines = []
    
    for item in working_results:
        if is_config:
            ip, lat, country, cfg_str = item
            clean_ips_for_file.append(cfg_str)
            telegram_lines.append(ip)
        else:
            target_str, lat, country = item
            clean_ips_for_file.append(target_str)
            # فقط آی‌پی بدون پورت در پیام‌رسان‌ها قرار می‌گیرد
            ip_only = target_str.split(":")[0]
            telegram_lines.append(ip_only)
            
    save_to_file(save_filename, "\n".join(clean_ips_for_file))
    
    if working_results or dead_count > 0:
        total_working = len(working_results)
        msg_lines = [
            f"{header_prefix}",
            f"Port Tested: {port_tested}",
            f"SNI / Domain: {SCAN_SETTINGS['domain']}\n"
        ]
        msg_lines.extend(telegram_lines)
        msg_lines.extend([
            f"\nTotal Working: {total_working} | Total Dead: {dead_count}",
            f"Clean IPs provided by:",
            f"Telegram Admin: {TELEGRAM_ID}",
            f"Rubika Admin: {RUBIKA_ID}"
        ])
        
        final_message = "\n".join(msg_lines)
        print(Colors.YELLOW + "\n[*] Sending results to messengers..." + Colors.END, flush=True)
        if send_to_all_messengers(final_message):
            print(Colors.GREEN + "[+] Messengers: Sent Successfully ✅" + Colors.END, flush=True)
        else:
            print(Colors.RED + "[-] Messengers: Failed to Send ❌" + Colors.END, flush=True)

def menu_option_1_mahsang():
    global stop_scan
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        input(Colors.BOLD + "\n[*] Press Enter..." + Colors.END)
        return
    
    configure_scanner_settings()
    
    port = SCAN_SETTINGS['port']
    domain = SCAN_SETTINGS['domain']
    timeout = SCAN_SETTINGS['timeout']
    workers = SCAN_SETTINGS['workers']
    
    stop_scan = False
    working_results = []
    dead_count = 0
    thread_lock = threading.Lock()
    
    print(Colors.YELLOW + f"\n[*] Scanning {len(ips)} IPs | Domain: {domain} | Port: {port} | Threads: {workers} | Timeout: {timeout}s..." + Colors.END, flush=True)
    
    def worker_task(ip):
        nonlocal dead_count
        if stop_scan:
            return
        lat = check_ip_mahsang_fronting(ip, port=port, domain=domain, timeout=timeout, path=SCAN_SETTINGS['path'])
        with thread_lock:
            if lat is not None:
                country = get_ip_country(ip)
                res_str = f"{ip}"
                working_results.append((res_str, lat, country))
                print(f"{ip:<22} | {str(lat)+'ms':<10} | {Colors.GREEN}[OK]{Colors.END}", flush=True)
            else:
                dead_count += 1
                print(f"{ip:<22} | {'Timeout':<10} | {Colors.RED}[TIMEOUT]{Colors.END}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = [executor.submit(worker_task, ip) for ip in ips]
            for f in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True

    header = f"📊 Scan Results\nMahsaNG & CDN Fronting (شیر و خورشید)"
    finalize_and_send(working_results, dead_count, header, port, "MahsaNG_CDN_IPs.txt")
    print(Colors.GREEN + f"\n[+] Scan finished! Working: {len(working_results)} | Dead: {dead_count}" + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter..." + Colors.END)

def menu_option_2_xray():
    global stop_scan
    raw_config = input(Colors.BOLD + "Enter Raw Config (VLESS / VMess / Trojan): " + Colors.END).strip()
    if not raw_config:
        return
    target_ip = input(Colors.BOLD + "Enter Target IP: " + Colors.END).strip()
    if not target_ip:
        return
        
    configure_scanner_settings()
    port = SCAN_SETTINGS['port']
    
    print(Colors.YELLOW + f"[*] Testing Config with IP {target_ip} on Port {port}..." + Colors.END, flush=True)
    
    lat = check_ip_mahsang_fronting(target_ip, port=port, domain=SCAN_SETTINGS['domain'], timeout=SCAN_SETTINGS['timeout'], path=SCAN_SETTINGS['path'])
    
    working_results = []
    dead_count = 0
    if lat is not None:
        country = get_ip_country(target_ip)
        new_cfg = raw_config
        
        ip_pattern = r'://([^@]+)@([^:]+):(\d+)'
        match = re.search(ip_pattern, new_cfg)
        if match:
            old_ip = match.group(2)
            old_port = match.group(3)
            new_cfg = new_cfg.replace(f"{old_ip}:{old_port}", f"{target_ip}:{port}")
        
        if "sni=" in new_cfg:
            new_cfg = re.sub(r'sni=[^&]+', f"sni={SCAN_SETTINGS['domain']}", new_cfg)
        else:
            separator = "&" if "?" in new_cfg else "?"
            new_cfg += f"{separator}sni={SCAN_SETTINGS['domain']}"
            
        if "host=" in new_cfg:
            new_cfg = re.sub(r'host=[^&]+', f"host={SCAN_SETTINGS['domain']}", new_cfg)

        working_results.append((target_ip, lat, country, new_cfg))
        print(f"{target_ip:<22} | {str(lat)+'ms':<10} | {Colors.GREEN}[CONNECTED & FIXED]{Colors.END}", flush=True)
    else:
        dead_count = 1
        print(f"{target_ip:<22} | {'Timeout':<10} | {Colors.RED}[TIMEOUT]{Colors.END}", flush=True)
        
    header = f"📊 Scan Results\nXray Config Dedicated Scanner"
    finalize_and_send(working_results, dead_count, header, port, "Xray_Config_Results.txt", is_config=True)
    print(Colors.GREEN + f"\n[+] Scan finished!" + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter..." + Colors.END)

def menu_option_3_edge():
    global stop_scan
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        input(Colors.BOLD + "\n[*] Press Enter..." + Colors.END)
        return
        
    configure_scanner_settings()
    
    port = SCAN_SETTINGS['port']
    domain = SCAN_SETTINGS['domain']
    timeout = SCAN_SETTINGS['timeout']
    workers = SCAN_SETTINGS['workers']
    
    stop_scan = False
    working_results = []
    dead_count = 0
    thread_lock = threading.Lock()
    
    print(Colors.YELLOW + f"\n[*] Starting Edge IP Scanner on {len(ips)} IPs..." + Colors.END, flush=True)
    
    def worker_task(ip):
        nonlocal dead_count
        if stop_scan:
            return
        lat = check_ip_mahsang_fronting(ip, port=port, domain=domain, timeout=timeout, path=SCAN_SETTINGS['path'])
        with thread_lock:
            if lat is not None:
                country = get_ip_country(ip)
                res_str = f"{ip}"
                working_results.append((res_str, lat, country))
                print(f"{ip:<22} | {str(lat)+'ms':<10} | {Colors.GREEN}[OK]{Colors.END}", flush=True)
            else:
                dead_count += 1
                print(f"{ip:<22} | {'Timeout':<10} | {Colors.RED}[TIMEOUT]{Colors.END}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = [executor.submit(worker_task, ip) for ip in ips]
            for f in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True

    header = f"📊 Scan Results\nEdge IP Scanner (Speed Test Mode)"
    finalize_and_send(working_results, dead_count, header, port, "Edge_Scanner_Results.txt")
    print(Colors.GREEN + f"\n[+] Scan finished! Working: {len(working_results)} | Dead: {dead_count}" + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter..." + Colors.END)

def main_menu():
    while True:
        print_banner()
        print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║ {Colors.GREEN}[1] MahsaNG & CDN Fronting Scanner (شیر و خورشید){Colors.CYAN}             ║
║ {Colors.YELLOW}[2] Xray Config Dedicated Scanner{Colors.CYAN}                          ║
║ {Colors.MAGENTA}[3] Edge IP Scanner (Speed Test){Colors.CYAN}                          ║
║ {Colors.END}{Colors.CYAN}[0] Exit{Colors.CYAN}                                                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
""", flush=True)
        choice = get_clean_input(Colors.BOLD + "[>] Select option: " + Colors.END)
        if choice == "1":
            menu_option_1_mahsang()
        elif choice == "2":
            menu_option_2_xray()
        elif choice == "3":
            menu_option_3_edge()
        elif choice == "0":
            print(Colors.YELLOW + "[*] Exiting..." + Colors.END, flush=True)
            sys.exit(0)
        else:
            print(Colors.RED + "[!] Invalid option." + Colors.END, flush=True)
            input(Colors.BOLD + "\n[*] Press Enter..." + Colors.END)
            os.system("clear")

if __name__ == "__main__":
    main_menu()
