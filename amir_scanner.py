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
BALE_BOT_TOKEN = "2690620:Nm1F_42X7P1ZMCg8VMMsQaMKDgDOEbSIvUk"
BALE_CHAT_ID = "5495275998"
IGAP_BOT_TOKEN = "C2487d0c-8f3c-40ba-b567-a38634788195"
IGAP_CHAT_ID = "@ipscanner"

TELEGRAM_ID = "@Pod66Mp"
RUBIKA_ID = "@Amir5880Om"

stop_scan = False
COUNTRY_CACHE = {}

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

def send_to_all_messengers(text):
    success_any = False
    for chunk in split_message_smart(text, max_length=3800):
        try:
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                res = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "disable_web_page_preview": True}, timeout=10)
                if res.status_code == 200: success_any = True
        except Exception: pass
        try:
            if RUBIKA_BOT_TOKEN and RUBIKA_CHAT_ID:
                res = requests.post(f"https://botapi.rubika.ir/v01/{RUBIKA_BOT_TOKEN}/sendMessage", json={"chat_id": RUBIKA_CHAT_ID, "text": chunk}, timeout=10)
                if res.status_code == 200: success_any = True
        except Exception: pass
        try:
            if BALE_BOT_TOKEN and BALE_CHAT_ID:
                res = requests.post(f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage", json={"chat_id": BALE_CHAT_ID, "text": chunk}, timeout=10)
                if res.status_code == 200: success_any = True
        except Exception: pass
        try:
            if IGAP_BOT_TOKEN and IGAP_CHAT_ID:
                res = requests.post("https://api.igap.net/v1/bot/sendMessage", json={"token": IGAP_BOT_TOKEN, "room_id": IGAP_CHAT_ID, "message": chunk}, timeout=10)
                if res.status_code == 200: success_any = True
        except Exception: pass
    return success_any

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

def check_ip_connection(ip, port=443, domain="speed.cloudflare.com", timeout=1.7, path="/"):
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
            
            payload = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {domain}\r\n"
                f"User-Agent: Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36\r\n"
                f"Connection: close\r\n\r\n"
            )
            tls_sock.sendall(payload.encode())
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
║ AMIR SCANNER PRO - CLEAN & FAST ENGINE                                   ║
╠══════════════════════════════════════════════════════════════════════════╣
║ {Colors.YELLOW}► Version :{Colors.WHITE} v3.1.0 (Custom Settings Mode){Colors.CYAN}                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner, flush=True)

def run_scanner_process(scanner_title, save_filename):
    global stop_scan
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        input(Colors.BOLD + "\n[*] Press Enter..." + Colors.END)
        return

    # تنظیمات پویا با مقادیر پیش‌فرض درخواست‌شده
    print(Colors.CYAN + "\n--- Scanner Configuration ---" + Colors.END, flush=True)
    try:
        domain_input = input(Colors.BOLD + "Enter SNI / Domain [Default: speed.cloudflare.com]: " + Colors.END).strip()
        domain = domain_input if domain_input else "speed.cloudflare.com"
        
        port_input = input(Colors.BOLD + "Enter Port [Default: 443]: " + Colors.END).strip()
        port = int(port_input) if port_input.isdigit() else 443

        workers_input = input(Colors.BOLD + "Enter Workers / Threads [Default: 20]: " + Colors.END).strip()
        workers = int(workers_input) if workers_input.isdigit() else 20
        
        timeout_input = input(Colors.BOLD + "Enter Timeout (seconds) [Default: 1.7]: " + Colors.END).strip()
        timeout = float(timeout_input) if timeout_input else 1.7
    except Exception:
        domain = "speed.cloudflare.com"
        port = 443
        workers = 20
        timeout = 1.7

    stop_scan = False
    working_results = []
    dead_count = 0
    thread_lock = threading.Lock()
    
    print(Colors.YELLOW + f"\n[*] Scanning {len(ips)} IPs | Domain: {domain} | Port: {port} | Threads: {workers} | Timeout: {timeout}s..." + Colors.END, flush=True)
    
    def worker_task(ip):
        nonlocal dead_count
        if stop_scan:
            return
        lat = check_ip_connection(ip, port=port, domain=domain, timeout=timeout, path="/")
        with thread_lock:
            if lat is not None:
                working_results.append((ip, lat))
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

    working_results.sort(key=lambda x: x[1])
    total_working = len(working_results)
    
    clean_ips_for_file = [item[0] for item in working_results]
    save_to_file(save_filename, "\n".join(clean_ips_for_file))

    if working_results:
        msg_lines = [f"📊 {scanner_title}", f"Port Tested: {port}", f"SNI / Domain: {domain}\n"]
        for ip, lat in working_results:
            msg_lines.append(ip)
        msg_lines.append(f"\nTotal Working: {total_working} | Total Dead: {dead_count}")
        msg_lines.append(f"Clean IPs provided by:\nTelegram Admin: {TELEGRAM_ID}\nRubika Admin: {RUBIKA_ID}")
        
        final_message = "\n".join(msg_lines)
        print(Colors.YELLOW + "\n[*] Sending clean results to messengers..." + Colors.END, flush=True)
        if send_to_all_messengers(final_message):
            print(Colors.GREEN + "[+] Messengers: Sent Successfully ✅" + Colors.END, flush=True)
        else:
            print(Colors.RED + "[-] Messengers: Failed to Send ❌" + Colors.END, flush=True)

    print(Colors.GREEN + f"\n[+] Scan finished! Working: {total_working} | Dead: {dead_count}" + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter..." + Colors.END)

def main_menu():
    while True:
        print_banner()
        print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║ {Colors.GREEN}[1] MahsaNG & CDN Fronting Scanner (شیر و خورشید){Colors.CYAN}             ║
║ {Colors.MAGENTA}[2] Edge IP Scanner (Speed Test){Colors.CYAN}                          ║
║ {Colors.END}{Colors.CYAN}[0] Exit{Colors.CYAN}                                                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
""", flush=True)
        choice = get_clean_input(Colors.BOLD + "[>] Select option: " + Colors.END)
        if choice == "1":
            run_scanner_process("MahsaNG & CDN Fronting (شیر و خورشید)", "MahsaNG_CDN_IPs.txt")
        elif choice == "2":
            run_scanner_process("Edge IP Scanner (Speed Test Mode)", "Edge_Scanner_Results.txt")
        elif choice == "0":
            print(Colors.YELLOW + "[*] Exiting..." + Colors.END, flush=True)
            sys.exit(0)
        else:
            print(Colors.RED + "[!] Invalid option." + Colors.END, flush=True)
            input(Colors.BOLD + "\n[*] Press Enter..." + Colors.END)
            os.system("clear")

if __name__ == "__main__":
    main_menu()
