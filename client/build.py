import subprocess
import os
import sys

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def log_info(message: str):
    print(f"{GREEN}[+] {message}{RESET}")

def log_error(message: str):
    print(f"{RED}[!] {message}{RESET}")

def log_section(title: str):
    print(f"{YELLOW}[+] --- {title} ---{RESET}")

def build_docker_image(dockerfile_dir: str, image_name: str):
    log_info(f"Starting Docker image build from: {dockerfile_dir}/Dockerfile")

    if not os.path.isdir(dockerfile_dir):
        log_error(f"Directory '{dockerfile_dir}' does not exist.")
        sys.exit(1)

    dockerfile_path = os.path.join(dockerfile_dir, "Dockerfile")
    if not os.path.isfile(dockerfile_path):
        log_error(f"Dockerfile not found at '{dockerfile_path}'.")
        sys.exit(1)

    try:
        result = subprocess.run(
            ["docker", "build", "-t", image_name, dockerfile_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        log_info("Docker image built successfully.")
        log_info(f"Image name: {image_name}")
        log_section("Build output")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        log_error("Failed to build Docker image.")
        log_section("Error output")
        print(e.stderr)
        sys.exit(e.returncode)
    except FileNotFoundError:
        log_error("Docker is not installed or not found in PATH.")
        sys.exit(1)

