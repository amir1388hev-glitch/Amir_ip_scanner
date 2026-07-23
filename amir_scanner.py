#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import json
import ipaddress
import os
import re
import socket
import ssl
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urlunparse, quote, unquote
import requests


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


GITHUB_IP_URL = "https://raw.githubusercontent.com/amir1388hev-glitch/termux_ip/main/Termux_ips"

DOWNLOAD_DIR = "/sdcard/Download"
SAVE_FILENAME = os.path.join(DOWNLOAD_DIR, "Amir_ip_scanner.txt")
LOCAL_ALL_IPS_FILE = os.path.join(DOWNLOAD_DIR, "all_ips.txt")

RUBIKA_BOT_TOKEN = "CABGDG0AGFFRWJKSBWBUBRUGGFMYNFITBVVDKTSVBNOKZWANYOITFQILZSSLCRKT"
RUBIKA_CHAT_ID = "g0ILUMK0562851bf38dfcd7703bdeb22"

TELEGRAM_BOT_TOKEN = "8851868234:AAFHxnxQ8AnHubsHtx0fNYtZ4mdGdUyXIoI"
TELEGRAM_CHAT_ID = "-1004437972136"

TELEGRAM_ID = "@Pod66Mp"
RUBIKA_ID = "@Amir5880Om"

# Global default settings for options 1-5
SCAN_SETTINGS = {
    "domain": "chatgpt.com",
    "path": "/",
    "port": 443,
    "timeout": 3.0,
    "workers": 20,
    "test_download": True
}

# Dedicated custom settings exclusively for Option 6 Scanner
CUSTOM_SCAN_SETTINGS = {
    "domain": "cloudflare.com",
    "path": "/",
    "port": 443,
    "timeout": 3.0,
    "workers": 20,
    "test_download": True
}

PORTS_TO_TEST = [
    443, 8443, 2053, 2083, 2087, 2096,
    80, 8080, 8880, 2052, 2082, 2086, 2095,
]

MAHSA_CDN_TYPES = {
    "1": "Cloudflare CDN",
    "2": "Akamai CDN",
    "3": "Fastly CDN",
    "4": "Bunny CDN",
    "5": "Any CDN (Mixed)"
}


def send_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    max_length = 4000
    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
    print(Colors.BLUE + "\n[*] Sending results to Telegram..." + Colors.END)
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
    max_length = 3500
    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
    print(Colors.BLUE + "[*] Sending results to Rubika..." + Colors.END)
    for chunk in chunks:
        payload = {"chat_id": RUBIKA_CHAT_ID, "text": chunk}
        try:
            requests.post(url, json=payload, timeout=12)
        except Exception:
            pass


def send_all(text):
    send_to_telegram(text)
    send_to_rubika(text)


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
            print(Colors.GREEN + f"[+] Loaded {len(ips)} IPs from GitHub repository." + Colors.END)
            return ips
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
                hosts = list(network.hosts())
                count = min(100, len(hosts))
                for i in range(count):
                    ips.append(str(hosts[i]))
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
                count = 0
                while current <= end and count < 100:
                    ips.append(str(current))
                    current += 1
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
    print(Colors.GREEN + f"[+] Loaded {len(ips)} IPs manually." + Colors.END)
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
    start_time = time.time()
    try:
        if port == 80:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            if test_download:
                request_data = f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nConnection: close\r\n\r\n"
                sock.sendall(request_data.encode())
                sock.recv(1024)
            latency = (time.time() - start_time) * 1000
            sock.close()
            return round(latency, 1)
        else:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            tls_sock = context.wrap_socket(sock, server_hostname=domain)
            
            if test_download:
                request_data = f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nConnection: close\r\n\r\n"
                tls_sock.sendall(request_data.encode())
                tls_sock.recv(1024)
                
            latency = (time.time() - start_time) * 1000
            tls_sock.close()
            return round(latency, 1)
    except Exception:
        return None


def check_ip_port_connection(ip, port, timeout=2.0):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def save_to_file(filepath, data):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
        print(Colors.GREEN + f"\n[+] Results saved to: {filepath}" + Colors.END)
    except Exception as e:
        print(Colors.RED + f"\n[!] Save error: {e}" + Colors.END)


def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
 ╔══════════════════════════════════════════════════════════════════╗
 ║                                                                  ║
 ║    █████╗ ███╗   ███╗██╗██████╗     ███████╗ ██████╗██╗███████╗  ║
 ║   ██╔══██╗████╗ ████║██║██╔══██╗    ██╔════╝██╔════╝██║██╔════╝  ║
 ║   ███████║██╔████╔██║██║██████╔╝    ███████╗██║     ██║█████╗    ║
 ║   ██╔══██║██║╚██╔╝██║██║██╔══██╗    ╚╚══██║██║     ██║██╔══╝    ║
 ║   ██║  ██║██║ ╚═╝ ██║██║██║  ██║    ███████║╚██████╗██║███████╗  ║
 ║   ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝╚══════╝  ║
 ║                                                                  ║
 ╠══════════════════════════════════════════════════════════════════╣
 ║  {Colors.YELLOW}► Version        :{Colors.WHITE} v1.0.2 (Mahsa & Shir-Khorshid) {Colors.CYAN} ║
 ║  {Colors.YELLOW}► Telegram Admin :{Colors.WHITE} {TELEGRAM_ID:<22}{Colors.CYAN}                 ║
 ║  {Colors.YELLOW}► Rubika Admin   :{Colors.WHITE} {RUBIKA_ID:<22}{Colors.CYAN}                 ║
 ╚══════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner)


def menu_option_1():
    print(Colors.YELLOW + "\n[>] Option 1: Test IP Health (Edge Speed Scanner)" + Colors.END)
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs available to test." + Colors.END)
        return

    total_ips = len(ips)
    working_ips = []
    completed_count = [0]
    failed_count = [0]

    print(Colors.BLUE + f"\n[*] Scanning {total_ips} IPs using {SCAN_SETTINGS['workers']} parallel workers...\n" + Colors.END)

    def worker_task(ip):
        lat = check_ip_http_latency(
            ip, port=SCAN_SETTINGS['port'], 
            domain=SCAN_SETTINGS['domain'], 
            timeout=SCAN_SETTINGS['timeout'], 
            test_download=SCAN_SETTINGS['test_download'], 
            path=SCAN_SETTINGS['path']
        )
        completed_count[0] += 1
        percent = int((completed_count[0] / total_ips) * 100)
        status_line = f"[*] Progress: {completed_count[0]}/{total_ips} ({percent}%) | Working: {len(working_ips)} | Failed: {failed_count[0]}"
        print(Colors.CYAN + f"\r{status_line:<70}" + Colors.END, end="", flush=True)

        if lat is not None:
            return (ip, lat)
        else:
            failed_count[0] += 1
            return None

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        futures = [executor.submit(worker_task, ip) for ip in ips]
        for future in as_completed(futures):
            res = future.result()
            if res:
                working_ips.append(res)

    print("\n" + "-" * 48)
    working_ips.sort(key=lambda x: x[1])
    output = "\n".join([item[0] for item in working_ips])
    save_to_file(SAVE_FILENAME, output)
    if working_ips:
        msg = f"Clean IPs:\n\n" + output + f"\n\nID: {TELEGRAM_ID} | {RUBIKA_ID}"
        send_all(msg)
    print(Colors.GREEN + f"\n[SUMMARY] Total: {total_ips} | Working: {len(working_ips)} | Failed: {failed_count[0]}" + Colors.END)


def menu_option_2():
    print(Colors.YELLOW + "\n[>] Option 2: Test IP and PORT with Latency" + Colors.END)
    ips = select_ip_source()
    if not ips: return
    tasks_list = [(ip, port) for ip in ips for port in PORTS_TO_TEST]
    total_combinations = len(tasks_list)
    completed_count = [0]
    results = []
    failed_count = [0]

    def worker_task(item):
        ip, port = item
        lat = check_ip_http_latency(ip, port=port, domain=SCAN_SETTINGS['domain'], timeout=SCAN_SETTINGS['timeout'], test_download=SCAN_SETTINGS['test_download'], path=SCAN_SETTINGS['path'])
        completed_count[0] += 1
        percent = int((completed_count[0] / total_combinations) * 100)
        status_line = f"[*] Progress: {completed_count[0]}/{total_combinations} ({percent}%) | Working: {len(results)} | Failed: {failed_count[0]}"
        print(Colors.CYAN + f"\r{status_line:<70}" + Colors.END, end="", flush=True)
        if lat is not None: return (f"{ip}:{port}", lat)
        else:
            failed_count[0] += 1
            return None

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        futures = [executor.submit(worker_task, t) for t in tasks_list]
        for future in as_completed(futures):
            res = future.result()
            if res: results.append(res)

    print("\n" + "-" * 55)
    results.sort(key=lambda x: x[1])
    output = "\n".join([item[0] for item in results])
    save_to_file(SAVE_FILENAME, output)
    if results: send_all(f"Healthy IPs:\n\n{output}\n\nID: {TELEGRAM_ID}")
    print(Colors.GREEN + f"\n[SUMMARY] Total: {total_combinations} | Working: {len(results)} | Failed: {failed_count[0]}" + Colors.END)


def menu_option_3():
    print(Colors.YELLOW + "\n[>] Option 3: Test TCP PORT Only" + Colors.END)
    ips = select_ip_source()
    if not ips: return
    tasks_list = [(ip, port) for ip in ips for port in PORTS_TO_TEST]
    total_combinations = len(tasks_list)
    completed_count = [0]
    results = []
    failed_count = [0]

    def worker_task(item):
        ip, port = item
        connected = check_ip_port_connection(ip, port, timeout=2.0)
        completed_count[0] += 1
        percent = int((completed_count[0] / total_combinations) * 100)
        status_line = f"[*] Progress: {completed_count[0]}/{total_combinations} ({percent}%) | Working: {len(results)} | Failed: {failed_count[0]}"
        print(Colors.CYAN + f"\r{status_line:<70}" + Colors.END, end="", flush=True)
        if connected: return f"{ip}:{port}"
        else:
            failed_count[0] += 1
            return None

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        futures = [executor.submit(worker_task, t) for t in tasks_list]
        for future in as_completed(futures):
            res = future.result()
            if res: results.append(res)

    print("\n" + "-" * 45)
    output = "\n".join(results)
    save_to_file(SAVE_FILENAME, output)
    if results: send_all(f"Open Ports:\n\n{output}\n\nID: {TELEGRAM_ID}")
    print(Colors.GREEN + f"\n[SUMMARY] Total: {total_combinations} | Working: {len(results)} | Failed: {failed_count[0]}" + Colors.END)


def menu_option_4():
    print(Colors.YELLOW + "\n[>] Option 4: Combine Config (Auto Send)" + Colors.END)
    raw_config = input(Colors.BOLD + "Config: " + Colors.END).strip()
    if not raw_config: return
    ips = select_ip_source()
    if not ips: return
    total_ips = len(ips)
    combined_results = []
    completed_count = [0]
    failed_count = [0]

    def worker_task(ip):
        lat = check_ip_http_latency(ip, port=443, domain="chatgpt.com", timeout=3.0)
        completed_count[0] += 1
        percent = int((completed_count[0] / total_ips) * 100)
        status_line = f"[*] Progress: {completed_count[0]}/{total_ips} ({percent}%) | Passed: {len(combined_results)} | Failed: {failed_count[0]}"
        print(Colors.CYAN + f"\r{status_line:<70}" + Colors.END, end="", flush=True)
        if lat is not None:
            return (f"vmess://...", lat)
        else:
            failed_count[0] += 1
            return None

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        futures = [executor.submit(worker_task, ip) for ip in ips]
        for future in as_completed(futures):
            res = future.result()
            if res: combined_results.append(res)
    print(Colors.GREEN + f"\n[SUMMARY] Total: {total_ips} | Passed: {len(combined_results)} | Failed: {failed_count[0]}" + Colors.END)


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

    total_ips = len(ips)
    working_ips = []
    completed_count = [0]
    failed_count = [0]

    print(Colors.BLUE + f"\n[*] Scanning {total_ips} IPs for {profile_name} using Fast Workers ({SCAN_SETTINGS['workers']})...\n" + Colors.END)

    def worker_task(ip):
        lat = check_ip_http_latency(
            ip, port=SCAN_SETTINGS['port'],
            domain=SCAN_SETTINGS['domain'],
            timeout=SCAN_SETTINGS['timeout'],
            test_download=SCAN_SETTINGS['test_download'],
            path=SCAN_SETTINGS['path']
        )
        completed_count[0] += 1
        percent = int((completed_count[0] / total_ips) * 100)
        
        status_line = f"[*] Progress: {completed_count[0]}/{total_ips} ({percent}%) | Working: {len(working_ips)} | Failed: {failed_count[0]}"
        print(Colors.CYAN + f"\r{status_line:<70}" + Colors.END, end="", flush=True)

        if lat is not None:
            return (ip, lat)
        else:
            failed_count[0] += 1
            return None

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        futures = [executor.submit(worker_task, ip) for ip in ips]
        for future in as_completed(futures):
            res = future.result()
            if res:
                working_ips.append(res)

    print("\n" + "-" * 48)
    working_ips.sort(key=lambda x: x[1])
    output = "\n".join([item[0] for item in working_ips])
    save_to_file(SAVE_FILENAME, output)

    if working_ips:
        msg = f"Mahsa/Shir-Khorshid Bypass IPs [{profile_name}]:\n\n" + output + f"\n\nID: {TELEGRAM_ID} | {RUBIKA_ID}"
        send_all(msg)

    print(Colors.GREEN + f"\n[SUMMARY] Total Tested: {total_ips} | Working: {len(working_ips)} | Failed: {failed_count[0]}" + Colors.END)


def menu_option_6_custom_scanner():
    print(Colors.YELLOW + "\n[>] Option 6: Custom Dedicated Scanner & Settings" + Colors.END)
    print(Colors.CYAN + "\n=== Custom Scanner Configuration ===" + Colors.END)
    print(f"1. Test Domain (SNI)  : {CUSTOM_SCAN_SETTINGS['domain']}")
    print(f"2. Test Path          : {CUSTOM_SCAN_SETTINGS['path']}")
    print(f"3. Port               : {CUSTOM_SCAN_SETTINGS['port']}")
    print(f"4. Timeout (s)        : {CUSTOM_SCAN_SETTINGS['timeout']}")
    print(f"5. Concurrent Workers : {CUSTOM_SCAN_SETTINGS['workers']}")
    print(f"6. Test Download      : {'Enabled' if CUSTOM_SCAN_SETTINGS['test_download'] else 'Disabled'}")
    
    choice = input(Colors.BOLD + "\nDo you want to change these custom settings before scanning? (y/N): " + Colors.END).strip().lower()
    if choice == 'y':
        d = input(f"Enter Test Domain [{CUSTOM_SCAN_SETTINGS['domain']}]: ").strip()
        if d: CUSTOM_SCAN_SETTINGS['domain'] = d
        p = input(f"Enter Port [{CUSTOM_SCAN_SETTINGS['port']}]: ").strip()
        if p.isdigit(): CUSTOM_SCAN_SETTINGS['port'] = int(p)
        t = input(f"Enter Timeout [{CUSTOM_SCAN_SETTINGS['timeout']}]: ").strip()
        try:
            if t: CUSTOM_SCAN_SETTINGS['timeout'] = float(t)
        except ValueError:
            pass
        w = input(f"Enter Concurrent Workers [{CUSTOM_SCAN_SETTINGS['workers']}]: ").strip()
        if w.isdigit(): CUSTOM_SCAN_SETTINGS['workers'] = int(w)
        print(Colors.GREEN + "[+] Custom settings updated successfully!" + Colors.END)

    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs available to scan." + Colors.END)
        return

    total_ips = len(ips)
    working_ips = []
    completed_count = [0]
    failed_count = [0]

    print(Colors.BLUE + f"\n[*] Running Custom Scanner on {total_ips} IPs using {CUSTOM_SCAN_SETTINGS['workers']} workers...\n" + Colors.END)

    def worker_task(ip):
        lat = check_ip_http_latency(
            ip, port=CUSTOM_SCAN_SETTINGS['port'],
            domain=CUSTOM_SCAN_SETTINGS['domain'],
            timeout=CUSTOM_SCAN_SETTINGS['timeout'],
            test_download=CUSTOM_SCAN_SETTINGS['test_download'],
            path=CUSTOM_SCAN_SETTINGS['path']
        )
        completed_count[0] += 1
        percent = int((completed_count[0] / total_ips) * 100)
        status_line = f"[*] Progress: {completed_count[0]}/{total_ips} ({percent}%) | Working: {len(working_ips)} | Failed: {failed_count[0]}"
        print(Colors.CYAN + f"\r{status_line:<70}" + Colors.END, end="", flush=True)

        if lat is not None:
            return (ip, lat)
        else:
            failed_count[0] += 1
            return None

    with ThreadPoolExecutor(max_workers=CUSTOM_SCAN_SETTINGS['workers']) as executor:
        futures = [executor.submit(worker_task, ip) for ip in ips]
        for future in as_completed(futures):
            res = future.result()
            if res:
                working_ips.append(res)

    print("\n" + "-" * 48)
    working_ips.sort(key=lambda x: x[1])
    output = "\n".join([item[0] for item in working_ips])
    save_to_file(SAVE_FILENAME, output)

    if working_ips:
        msg = f"Custom Scanner Results (Domain: {CUSTOM_SCAN_SETTINGS['domain']}):\n\n" + output + f"\n\nID: {TELEGRAM_ID} | {RUBIKA_ID}"
        send_all(msg)

    print(Colors.GREEN + f"\n[SUMMARY] Total: {total_ips} | Working: {len(working_ips)} | Failed: {failed_count[0]}" + Colors.END)


def main_menu():
    while True:
        print_banner()
        print(Colors.CYAN + """
 ╔══════════════════════════════════════════════════════════════════╗
 ║  [1] Test IP Health (Edge Speed & Download Test)               ║
 ║  [2] Test IP and PORT with Latency Table                        ║
 ║  [3] Test TCP PORT Only                                         ║
 ║  [4] Combine Config (Auto Send to Telegram & Rubika)            ║
 ║  [5] Mahsa & Shir-Khorshid VPN Special CDN Scanner              ║
 ║  [6] Custom Dedicated Scanner & Settings (NEW!)                 ║
 ║  [0] Exit                                                       ║
 ╚══════════════════════════════════════════════════════════════════╝
""" + Colors.END)

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
        elif choice == "0":
            print(Colors.YELLOW + "[*] Exiting program..." + Colors.END)
            sys.exit(0)
        else:
            print(Colors.RED + "[!] Invalid option selected." + Colors.END)

        input(Colors.BOLD + "\n[*] Press Enter to continue..." + Colors.END)
        os.system("clear")


if __name__ == "__main__":
    main_menu()
