import random
import string
import time
import subprocess
import tempfile
import os
from pathlib import Path
from colorama import Fore,Style
import zipfile
import sys

def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def run_command(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Error running {' '.join(cmd)}: {result.stderr}")
    return result.stdout

def run_command_no_output(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Error running {' '.join(cmd)}: {result.stderr}")

def encode_file(filepath):
    import base64
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_code_repo_from_env():
    home = str(Path.home())
    env_path = os.path.join(home, ".sectyra", "codespace_data", ".env")
    if not os.path.isfile(env_path):
        raise RuntimeError(f".env file not found in {env_path}")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("CODE_REPO="):
                return line.strip().split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("CODE_REPO variable not found in .env file")

def start_codespace():
    CODE_REPO = get_code_repo_from_env()
    random_name = ''.join(random.choices(string.ascii_lowercase, k=8))
    
    hide_cursor()
    print(f"{Fore.YELLOW}[+]{Style.RESET_ALL}{Fore.WHITE} Creating codespace with name{Style.RESET_ALL}: {Fore.RED}{random_name}{Style.RESET_ALL}")
    run_command_no_output([
        "gh", "cs", "create", "--repo", CODE_REPO,
        "--machine", "basicLinux32gb", "--display-name", random_name
    ])

    print(f"{Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}Waiting for codespace to be ready...{Style.RESET_ALL}")
    time.sleep(10)

    output = run_command(["gh", "cs", "ls"])
    codespace_name = None
    for line in output.splitlines():
        if random_name in line:
            codespace_name = line.split()[0]
            break

    if not codespace_name:
        raise RuntimeError(f"Codespace with name {random_name} not found")

    # Use user config in ~/.sectyra/codespace_data
    home = str(Path.home())
    user_codespace_data = os.path.join(home, ".sectyra", "codespace_data")
    if not os.path.isdir(user_codespace_data):
        raise RuntimeError(f"Config folder does not exist in {user_codespace_data}")

    print(f"{Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}Creating code_data.zip from user configuration...{Style.RESET_ALL}")
    zip_path = "code_data.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(user_codespace_data):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, user_codespace_data)
                zipf.write(abs_path, os.path.join("codespace_data", rel_path))

    print(f"{Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}Encoding code_data.zip...{Style.RESET_ALL}")
    time.sleep(10)

    encoded_file = encode_file("code_data.zip")

    script_content = f"""#!/bin/bash
echo "{encoded_file}" | base64 -d > /home/codespace/code_data.zip
sudo apt update
sudo apt install moreutils cron tmux curl -y
unzip -o /home/codespace/code_data.zip -d /home/codespace/
sudo bash -c 'cat /home/codespace/codespace_data/crontab >> /etc/crontab'
echo {codespace_name} > /tmp/name.tmp
sudo mv /tmp/name.tmp /opt/.code_name
echo 1 > /tmp/id.tmp
sudo mv /tmp/id.tmp /opt/.code_id

set -a 
source /home/codespace/codespace_data/.env
set +a

echo \"source /home/codespace/codespace_data/.env\" >> /home/codespace/.bashrc

echo $GIT_TOKEN | gh auth login --hostname github.com --with-token ; sleep 2
rm /home/codespace/code_data.zip

sudo service cron start

cd /opt
curl -LO https://github.com/projectdiscovery/notify/releases/download/v1.0.7/notify_1.0.7_linux_amd64.zip
unzip -o notify_1.0.7_linux_amd64.zip
sudo mv notify /usr/bin/notify
mkdir -p /home/codespace/.config/notify

sleep 2

envsubst < /home/codespace/codespace_data/.notify.yaml > /home/codespace/.config/notify/provider-config.yaml
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_script:
        temp_script.write(script_content)
        local_script_path = temp_script.name

    remote_script_path = "/home/codespace/remote_install.sh"

    install_script = encode_file(local_script_path)

    print(f"{Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}Uploading and running remote install script...{Style.RESET_ALL}")
    run_command_no_output([
        "gh", "cs", "ssh","-c", codespace_name, "--",f"echo {install_script} | base64 -d >> {remote_script_path}"
    ])

    run_command_no_output([
        "gh", "cs", "ssh", "-c", codespace_name,
        "--", f"sleep 10 && bash {remote_script_path}"
    ])

    os.remove(local_script_path)
    if os.path.exists("code_data.zip"):
        os.remove("code_data.zip")
        print(f"{Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}Deleted local code_data.zip{Style.RESET_ALL}")

    print(f"{Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}Starting runner in codespace...{Style.RESET_ALL}")
    subprocess.run([
        "gh","cs","ssh","-c",codespace_name,"--","cd /home/codespace/codespace_data && tmux new-session -d -s myrunner 'bash /home/codespace/codespace_data/runner.sh'"
    ])

    show_cursor()
