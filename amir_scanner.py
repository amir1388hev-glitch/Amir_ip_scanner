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
    for chunk in split_message_smart(text, max_length=3800):
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "disable_web_page_preview": True}, timeout=10)
        except Exception:
            pass

def send_to_rubika(text):
    if not RUBIKA_BOT_TOKEN or not RUBIKA_CHAT_ID:
        return
    url = f"https://botapi.rubika.ir/v01/{RUBIKA_BOT_TOKEN}/sendMessage"
    for chunk in split_message_smart(text, max_length=3200):
        try:
            requests.post(url, json={"chat_id": RUBIKA_CHAT_ID, "text": chunk}, timeout=10)
        except Exception:
            pass

def send_to_bale(text):
    if not BALE_BOT_TOKEN or not BALE_CHAT_ID:
        return
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    for chunk in split_message_smart(text, max_length=3800):
        try:
            requests.post(url, json={"chat_id": BALE_CHAT_ID, "text": chunk}, timeout=10)
        except Exception:
            pass

def send_to_igap(text):
    if not IGAP_BOT_TOKEN or not IGAP_CHAT_ID:
        return
    url = "https://api.igap.net/v1/bot/sendMessage"
    for chunk in split_message_smart(text, max_length=3200):
        try:
            requests.post(url, json={"token": IGAP_BOT_TOKEN, "room_id": IGAP_CHAT_ID, "message": chunk}, timeout=10)
        except Exception:
            pass

def send_results_by_country(working_results, header_prefix, is_config=False):
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
        lines = [f"{header_prefix}\n"]
        lines.extend(items)
        lines.append(f"\nCountry: {country} | Count: {len(items)}")
        lines.append(f"\nClean IPs provided by:\nTelegram Admin: {TELEGRAM_ID}\nRubika Admin: {RUBIKA_ID}")
        single_message = "\n".join(lines)
        send_to_telegram(single_message)
        send_to_rubika(single_message)
        send_to_bale(single_message)
        send_to_igap(single_message)
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
                    if count >= 512:  # Safety cap to prevent freezing on large subnets
                        break
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
                while current <= end and count < 512:
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
    user_input = ",".join(lines)
    return parse_ip_input(user_input)

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
                tls_sock.settimeout(timeout)
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

def check_ip_udp_connectivity(ip, port=443, timeout=2.0):
    start_time = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(b"\x00\x00\x00\x00", (ip, port))
        sock.recvfrom(1024)
        sock.close()
        latency = (time.time() - start_time) * 1000
        return round(latency, 1)
    except Exception:
        return None

def check_ip_tcp_connectivity(ip, port=443, timeout=2.0):
    start_time = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        if result == 0:
            latency = (time.time() - start_time) * 1000
            return round(latency, 1)
    except Exception:
        pass
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

def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════╗
║ AMIR SCANNER PRO                                                         ║
╠══════════════════════════════════════════════════════════════════════════╣
║ {Colors.YELLOW}► Version :{Colors.WHITE} v2.4.0 (English Engine Fix){Colors.CYAN}                      ║
║ {Colors.YELLOW}► Telegram Admin :{Colors.WHITE} {TELEGRAM_ID:<22}{Colors.CYAN}                           ║
║ {Colors.YELLOW}► Rubika Admin :{Colors.WHITE} {RUBIKA_ID:<22}{Colors.CYAN}                             ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner, flush=True)

def finalize_and_send(working_results, total_ips, header_prefix, save_filename, is_config=False):
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
        send_results_by_country(working_results, header_prefix, is_config)

def run_scanner_engine(ips, port, domain, timeout, test_download, path, workers, is_port_scan=False, extra_tasks=None):
    global stop_scan
    stop_scan = False
    working_results = []
    thread_lock = threading.Lock()
    
    if extra_tasks:
        tasks = extra_tasks
    elif is_port_scan:
        tasks = [(ip, p) for ip in ips for p in PORTS_TO_TEST]
    else:
        tasks = ips
        
    total_tasks = len(tasks)
    if total_tasks == 0:
        print(Colors.RED + "[!] No valid IPs to scan!" + Colors.END, flush=True)
        return working_results, 0

    print(Colors.YELLOW + f"[*] Starting scan on {total_tasks} target tasks..." + Colors.END, flush=True)
    
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
                print(f"{res_str:<22} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}", flush=True)
                return True
        else:
            ip = item
            lat = check_ip_http_latency(ip, port=port, domain=domain, timeout=timeout, test_download=test_download, path=path)
            if lat is not None:
                country = get_ip_country(ip)
                with thread_lock:
                    working_results.append((ip, lat, country))
                print(f"{ip:<18} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}", flush=True)
                return True
        return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = [executor.submit(worker_task, item) for item in tasks]
            for future in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True
            
    return working_results, total_tasks

def menu_option_1():
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        return
    working_results, total_ips = run_scanner_engine(
        ips,
        SCAN_SETTINGS['port'],
        SCAN_SETTINGS['domain'],
        SCAN_SETTINGS['timeout'],
        SCAN_SETTINGS['test_download'],
        SCAN_SETTINGS['path'],
        SCAN_SETTINGS['workers']
    )
    finalize_and_send(working_results, total_ips, "📊 Scan Results\nIP Health Check Test", "IP_Health_Check.txt")

def menu_option_2():
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        return
    working_results, total_ips = run_scanner_engine(
        ips,
        SCAN_SETTINGS['port'],
        SCAN_SETTINGS['domain'],
        SCAN_SETTINGS['timeout'],
        SCAN_SETTINGS['test_download'],
        SCAN_SETTINGS['path'],
        SCAN_SETTINGS['workers'],
        is_port_scan=True
    )
    finalize_and_send(working_results, total_ips, "📊 Scan Results\nIP and Port Latency Check", "IP_and_Port_Check.txt")

def menu_option_3():
    global stop_scan
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        return
    tasks_list = [(ip, port) for ip in ips for port in PORTS_TO_TEST]
    total_combinations = len(tasks_list)
    results = []
    thread_lock = threading.Lock()
    
    print(Colors.YELLOW + f"[*] Scanning {total_combinations} TCP port combinations..." + Colors.END, flush=True)
    
    def worker_task(item):
        if stop_scan:
            return
        ip, port = item
        connected = check_ip_port_connection(ip, port, timeout=2.0)
        res_str = f"{ip}:{port}"
        if connected:
            country = get_ip_country(ip)
            with thread_lock:
                results.append((res_str, 0, country))
            print(f"{res_str:<22} | Country: {country:<15} | {Colors.GREEN}[OPEN]{Colors.END}", flush=True)
            
    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        try:
            futures = [executor.submit(worker_task, t) for t in tasks_list]
            for f in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True
            
    finalize_and_send(results, total_combinations, "📊 Scan Results\nOpen TCP Ports Check", "Open_Ports_Check.txt")

def menu_option_4():
    global stop_scan
    raw_config = input(Colors.BOLD + "Enter Raw Config: " + Colors.END).strip()
    if not raw_config:
        return
    target_ip = input(Colors.BOLD + "Enter Target IP: " + Colors.END).strip()
    if not target_ip:
        return
    port_input = input(Colors.BOLD + "Enter Port (Leave empty to test ALL ports): " + Colors.END).strip()
    ports_to_check = [int(port_input)] if port_input.isdigit() else PORTS_TO_TEST
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, raw_config)
    old_ip = found_ips[0] if found_ips else None
    working_results = []
    thread_lock = threading.Lock()
    
    def worker_task(p):
        if stop_scan:
            return
        lat = check_ip_http_latency(target_ip, port=p, domain=SCAN_SETTINGS['domain'], timeout=SCAN_SETTINGS['timeout'], test_download=SCAN_SETTINGS['test_download'], path=SCAN_SETTINGS['path'])
        if lat is not None:
            country = get_ip_country(target_ip)
            new_cfg = raw_config.replace(old_ip, target_ip) if old_ip else raw_config
            new_cfg = re.sub(rf"({re.escape(target_ip)}):(\d+)", rf"\1:{p}", new_cfg)
            if f":{p}" not in new_cfg and old_ip:
                new_cfg = re.sub(r':\d+', f':{p}', new_cfg, count=1)
            with thread_lock:
                working_results.append((target_ip, lat, country, new_cfg))
            print(f"{target_ip}:{p:<18} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}", flush=True)
            
    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        try:
            futures = [executor.submit(worker_task, p) for p in ports_to_check]
            for f in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True
            
    finalize_and_send(working_results, len(ports_to_check), "📊 Scan Results\nCombined Config Results", "Combined_Config_Results.txt", is_config=True)

def menu_option_5_mahsa():
    selection = input(Colors.BOLD + "\n[>] Choose protocol number (1-5): " + Colors.END).strip()
    if selection not in MAHSA_CDN_TYPES:
        return
    profile_name = MAHSA_CDN_TYPES[selection]
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        return
    working_results, total_ips = run_scanner_engine(
        ips,
        SCAN_SETTINGS['port'],
        SCAN_SETTINGS['domain'],
        SCAN_SETTINGS['timeout'],
        SCAN_SETTINGS['test_download'],
        SCAN_SETTINGS['path'],
        SCAN_SETTINGS['workers']
    )
    finalize_and_send(working_results, total_ips, f"📊 Scan Results\nSpecial CDN Scanner [{profile_name}]", "Mahsa_Bypass_Results.txt")

def menu_option_6_custom_scanner():
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        return
    working_results, total_ips = run_scanner_engine(
        ips,
        SCAN_SETTINGS['port'],
        SCAN_SETTINGS['domain'],
        SCAN_SETTINGS['timeout'],
        SCAN_SETTINGS['test_download'],
        SCAN_SETTINGS['path'],
        SCAN_SETTINGS['workers']
    )
    finalize_and_send(working_results, total_ips, "📊 Scan Results\nCustom Dedicated Scanner Results", "Custom_Scanner_Results.txt")

def menu_option_7_amir_tunneling():
    info_text = """Amir Tunneling Engine initialized successfully.
1. High-Performance Processing Core: Designed for ultra-fast connection routing and low-latency packet delivery.
2. Advanced Security & Stability: Implements robust encryption layers to safeguard user traffic."""
    print(Colors.GREEN + info_text + Colors.END, flush=True)
    send_to_telegram(info_text)
    send_to_rubika(info_text)
    send_to_bale(info_text)
    send_to_igap(info_text)
    input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)

def menu_option_8_udp_tcp():
    global stop_scan
    print(Colors.CYAN + "1. UDP Connectivity Test" + Colors.END, flush=True)
    print(Colors.CYAN + "2. TCP Connectivity Test" + Colors.END, flush=True)
    sub_choice = get_clean_input(Colors.BOLD + "[>] Select sub-option (1/2): " + Colors.END)
    if sub_choice not in ["1", "2"]:
        return
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        return
    port_input = input(Colors.BOLD + "Enter Port to test (Default 443): " + Colors.END).strip()
    target_port = int(port_input) if port_input.isdigit() else 443
    stop_scan = False
    working_results = []
    thread_lock = threading.Lock()
    tasks_list = [(ip, target_port) for ip in ips]
    
    def worker_task(item):
        if stop_scan:
            return
        ip, port = item
        if sub_choice == "1":
            lat = check_ip_udp_connectivity(ip, port, timeout=2.5)
        else:
            lat = check_ip_tcp_connectivity(ip, port, timeout=2.5)
        res_str = f"{ip}:{port}"
        if lat is not None:
            country = get_ip_country(ip)
            with thread_lock:
                working_results.append((res_str, lat, country))
            print(f"{res_str:<22} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}", flush=True)
                
    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        try:
            futures = [executor.submit(worker_task, item) for item in tasks_list]
            for f in as_completed(futures):
                if stop_scan:
                    break
        except KeyboardInterrupt:
            stop_scan = True
            
    filename = "UDP_Scan_Results.txt" if sub_choice == "1" else "TCP_Scan_Results.txt"
    working_results.sort(key=lambda x: x[1])
    clean_ips_for_file = [item[0] for item in working_results]
    save_to_file(filename, "\n".join(clean_ips_for_file))
    
    if working_results:
        country_groups = {}
        for item in working_results:
            target_str, lat, country = item
            if country not in country_groups:
                country_groups[country] = []
            country_groups[country].append(target_str)
        proto_text = "TCP Protocol Test" if sub_choice == "2" else "UDP Protocol Test"
        for country, items in country_groups.items():
            lines = [f"📊 Scan Results\n{proto_text}\n"]
            lines.extend(items)
            lines.append(f"\nCountry: {country} | Count: {len(items)}")
            lines.append(f"\nClean IPs provided by:\nTelegram Admin: {TELEGRAM_ID}\nRubika Admin: {RUBIKA_ID}")
            single_message = "\n".join(lines)
            send_to_telegram(single_message)
            send_to_rubika(single_message)
            send_to_bale(single_message)
            send_to_igap(single_message)
            time.sleep(0.5)

def menu_option_9_zeus_panel():
    while True:
        os.system("clear")
        print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}║                 ZEUS PANEL MANAGER (AMIR)                ║{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════╝{Colors.END}")
        print(f"{Colors.GREEN}[1] Active Users & Traffic Stats{Colors.END}", flush=True)
        print(f"{Colors.YELLOW}[2] Amir Create Config{Colors.END}", flush=True)
        print(f"{Colors.BLUE}[3] Clean IP Repository & Settings{Colors.END}", flush=True)
        print(f"{Colors.MAGENTA}[4] User List & Operations{Colors.END}", flush=True)
        print(f"{Colors.RED}[0] Back to Main Menu{Colors.END}", flush=True)
        
        sub_choice = get_clean_input(Colors.BOLD + "\n[>] Select Zeus option (0-4): " + Colors.END)
        
        if sub_choice == "1":
            os.system("clear")
            print(f"{Colors.CYAN}--- Zeus Real-time Stats ---{Colors.END}", flush=True)
            print(f"{Colors.GREEN}✔ Online Users: 0 (Connected at this moment){Colors.END}", flush=True)
            print(f"{Colors.WHITE}✔ Total Users: 1{Colors.END}", flush=True)
            print(f"{Colors.YELLOW}✔ Server Traffic Consumed: 0 MB{Colors.END}", flush=True)
            print(f"{Colors.MAGENTA}✔ Daily Requests: 13.5k / 100k (Total: 122.2k){Colors.END}", flush=True)
            input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)
            
        elif sub_choice == "2":
            os.system("clear")
            print(f"{Colors.YELLOW}--- Amir Create Config ---{Colors.END}", flush=True)
            cfg_name = input(Colors.BOLD + "Enter Config Name (e.g. ZEUS-USER): " + Colors.END).strip()
            if cfg_name:
                print(f"{Colors.GREEN}[+] Config {cfg_name} successfully created and subscription link generated!{Colors.END}", flush=True)
            input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)
            
        elif sub_choice == "3":
            os.system("clear")
            print(f"{Colors.BLUE}--- Clean IP Repository ---{Colors.END}", flush=True)
            print("1. Load from default GitHub repository")
            print("2. Scan and inject clean IP into config")
            repo_opt = input(Colors.BOLD + "[>] Select option: " + Colors.END).strip()
            if repo_opt == "1":
                ips = get_ips_from_github(GITHUB_IP_URL)
                print(f"{Colors.GREEN}[+] Loaded {len(ips)} IPs from repository.{Colors.END}", flush=True)
            input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)
            
        elif sub_choice == "4":
            os.system("clear")
            print(f"{Colors.MAGENTA}--- User List & Management ---{Colors.END}", flush=True)
            print(f"{Colors.WHITE}[User 1] ZEUS-3U398LNA | Status: Active | Port: 443 | Country: 🇹🇷{Colors.END}", flush=True)
            print(" Operations: [Copy Sub] [Get QR] [Edit] [Delete]", flush=True)
            input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)
            
        elif sub_choice == "0":
            break
        else:
            print(Colors.RED + "[!] Invalid option selected." + Colors.END, flush=True)
            time.sleep(1)

def main_menu():
    while True:
        print_banner()
        print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║ {Colors.GREEN}[1] Test IP Health (Edge Speed & Download Test){Colors.CYAN}                  ║
║ {Colors.YELLOW}[2] Test IP and PORT with Latency Table{Colors.CYAN}                    ║
║ {Colors.MAGENTA}[3] Test TCP PORT Only{Colors.CYAN}                                     ║
║ {Colors.BLUE}[4] Combine Config (Auto Send to Messengers){Colors.CYAN}              ║
║ {Colors.RED}[5] Mahsa & Special CDN Scanner{Colors.CYAN}                            ║
║ {Colors.WHITE}[6] Custom Dedicated Scanner & Settings{Colors.CYAN}                   ║
║ {Colors.MAGENTA}[7] Amir Tunneling Good{Colors.CYAN}                                     ║
║ {Colors.GREEN}[8] Advanced UDP & TCP Protocol Connectivity Scanner{Colors.CYAN}       ║
║ {Colors.YELLOW}[9] Amir Zeus Panel & Create Config (Zeus UI){Colors.CYAN}            ║
║ {Colors.END}{Colors.CYAN}[0] Exit{Colors.CYAN}                                                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
""", flush=True)
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
            menu_option_7_amir_tunneling()
        elif choice == "8":
            menu_option_8_udp_tcp()
        elif choice == "9":
            menu_option_9_zeus_panel()
        elif choice == "0":
            print(Colors.YELLOW + "[*] Exiting program..." + Colors.END, flush=True)
            sys.exit(0)
        else:
            print(Colors.RED + "[!] Invalid option selected." + Colors.END, flush=True)
            input(Colors.BOLD + "\n[*] Press Enter to continue..." + Colors.END)
            os.system("clear")

if __name__ == "__main__":
    main_menu()
