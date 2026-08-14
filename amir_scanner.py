#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ipaddress
import os
import re
import socket
import ssl
import sys
import time
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

TELEGRAM_ID = "@Pod66Mp"
RUBIKA_ID = "@Amir5880Om"

SCAN_SETTINGS = {
    "domain": "speed.cloudflare.com",
    "timeout": 4.0,
    "workers": 10
}

stop_scan = False
COUNTRY_CACHE = {}

def test_ip_connection(ip, port=443, domain="speed.cloudflare.com", timeout=4.0):
    """
    تست اتصال TCP و هندشیک TLS با SNI اختصاصی speed.cloudflare.com
    """
    start_time = time.time()
    try:
        # مرحله اول: تست سوکت TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        if result != 0:
            sock.close()
            return None
        
        # مرحله دوم: اگر پورت 443 یا پورت‌های امن بود، تست TLS با SNI جدید
        if port in [443, 8443, 2053, 2083, 2087, 2096]:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                pass
        sock.close()
        
        latency = (time.time() - start_time) * 1000
        return round(latency, 1)
    except Exception:
        pass
    return None

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

def send_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": True}, timeout=10)
    except Exception:
        pass

def get_clean_input(prompt_text):
    try:
        return input(prompt_text).strip()
    except (KeyboardInterrupt, EOFError):
        print("\n[*] Exiting...", flush=True)
        sys.exit(0)

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
                count = 0
                for ip in network.hosts():
                    ips.append(str(ip))
                    count += 1
                    if count >= 256:
                        break
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
                lines = f.readlines()
            raw_ips = []
            for line in lines:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("#"):
                    ip_part = clean_line.split()[0].split(":")[0]
                    raw_ips.append(ip_part)
            if raw_ips:
                return parse_ip_input(",".join(raw_ips))
        except Exception:
            pass
    return []

def get_manual_ips():
    print(Colors.CYAN + "\nEnter IPs (single IP, range, CIDR, or multiline paste, press Enter twice to finish):" + Colors.END, flush=True)
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
    return parse_ip_input(",".join(lines))

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
║ AMIR SCANNER PRO - SPEED CLOUDFLARE SNI EDITION                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║ {Colors.YELLOW}► SNI Domain :{Colors.WHITE} speed.cloudflare.com{Colors.CYAN}                      ║
║ {Colors.YELLOW}► Telegram Admin :{Colors.WHITE} {TELEGRAM_ID:<22}{Colors.CYAN}                           ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner, flush=True)

def run_scanner_engine(ips, port):
    global stop_scan
    stop_scan = False
    working_results = []
    thread_lock = threading.Lock()
    
    total_tasks = len(ips)
    if total_tasks == 0:
        print(Colors.RED + "[!] No valid IPs to scan!" + Colors.END, flush=True)
        return working_results

    print(Colors.YELLOW + f"[*] Scanning {total_tasks} IPs on Port {port} with SNI: speed.cloudflare.com..." + Colors.END, flush=True)
    
    def worker_task(ip):
        if stop_scan:
            return
        lat = test_ip_connection(ip, port=port, domain=SCAN_SETTINGS['domain'], timeout=SCAN_SETTINGS['timeout'])
        if lat is not None:
            country = get_ip_country(ip)
            with thread_lock:
                working_results.append((ip, lat, country))
            print(f"{ip:<18} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}", flush=True)

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        try:
            futures = [executor.submit(worker_task, ip) for ip in ips]
            for future in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True
            print(Colors.YELLOW + "\n[*] Scan interrupted." + Colors.END, flush=True)
            
    return working_results

def main_menu():
    while True:
        print_banner()
        print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║ {Colors.GREEN}[1] Start IP Scanner (Custom Port & Speed.cloudflare.com){Colors.CYAN}  ║
║ {Colors.END}{Colors.CYAN}[0] Exit{Colors.CYAN}                                                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
""", flush=True)
        choice = get_clean_input(Colors.BOLD + "[>] Select option: " + Colors.END)
        if choice == "1":
            # پرسش پورت از کاربر
            port_input = get_clean_input(Colors.BOLD + "[>] Enter target Port (e.g. 443, 8443, 2053): " + Colors.END)
            try:
                target_port = int(port_input)
            except ValueError:
                target_port = 443
                print(Colors.YELLOW + "[!] Invalid port, defaulting to 443." + Colors.END, flush=True)
            
            ips = select_ip_source()
            if ips:
                working_results = run_scanner_engine(ips, target_port)
                working_results.sort(key=lambda x: x[1])
                
                clean_ips = [item[0] for item in working_results]
                save_to_file("working_speed_ips.txt", "\n".join(clean_ips))
                
                print(Colors.GREEN + f"\n[+] Scan finished! Total working IPs: {len(working_results)}" + Colors.END, flush=True)
                if working_results:
                    send_to_telegram(f"📊 Speed Cloudflare Scan Results (Port {target_port}):\n" + "\n".join(clean_ips[:20]))
            input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)
        elif choice == "0":
            sys.exit(0)

if __name__ == "__main__":
    main_menu()
