import subprocess
import sys
import getpass
from colorama import init, Fore, Style

init(autoreset=True)

def log_info(message: str):
    print(f"{Fore.GREEN}[+] {message}{Style.RESET_ALL}")

def log_error(message: str):
    print(f"{Fore.RED}[!] {message}{Style.RESET_ALL}")

def docker_login(registry: str, username: str, password: str):
    try:
        subprocess.run(
            ["docker", "login", registry, "-u", username, "--password-stdin"],
            input=password,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        log_info(f"Login successful to {registry}")
    except subprocess.CalledProcessError as e:
        log_error(f"Login failed to {registry}")
        print(e.stderr)
        sys.exit(1)

def upload_image(image_name: str, target: str):
    print(f"{Fore.CYAN}Enter credentials for {target}:{Style.RESET_ALL}")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    if target == "ghcr":
        registry = "ghcr.io"
        tagged_image = f"{registry}/{username}/{image_name}"
    elif target == "dockerhub":
        registry = "docker.io"
        tagged_image = f"{username}/{image_name}"
    else:
        log_error(f"Unknown target: {target}")
        sys.exit(1)

    docker_login(registry, username, password)

    try:
        subprocess.run(["docker", "tag", image_name, tagged_image], check=True)
        result = subprocess.run(
            ["docker", "push", tagged_image],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        log_info(f"Image pushed successfully to {target}")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to push image: {tagged_image}")
        print(e.stderr)
        sys.exit(1)


