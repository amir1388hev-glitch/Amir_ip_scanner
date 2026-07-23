#!/bin/bash

# Clear screen
clear

echo -e "\033[92m[*] Installing Amir IP Scanner dependencies...\033[95m"

# Update and install python and git if needed
pkg update -y && pkg upgrade -y
pkg install python git -y

# Install required python modules
pip install requests

# Create directory if not exists
mkdir -p $HOME/amir_scanner
cd $HOME/amir_scanner

# Download the main python script from GitHub
echo -e "\033[94m[*] Downloading scanner script...\033[0m"
curl -s -L -o amir_scanner.py "https://raw.githubusercontent.com/amir1388hev-glitch/amir_ip_scanner/main/amir_scanner.py"

# Make it executable or ready to run
clear
echo -e "\033[92m[+] Installation completed successfully!\033[0m"
echo -e "\033[93mTo run the scanner, type: \033[96mpython3 amir_scanner.py\033[0m"
