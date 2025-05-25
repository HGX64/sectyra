import argparse
import os
import shutil
from pathlib import Path
from client.build import build_docker_image
from client.upload import upload_image
from client.start import start_codespace
from colorama import Fore,Style
import pyfiglet

def create_description_with_banner():
    ascii_banner = pyfiglet.figlet_format("Sectyra",font="slant")
    colored_banner = Fore.BLUE + ascii_banner + Style.RESET_ALL
    description = colored_banner + "\n" + "Sectyra - Workflow and Docker management tool"
    return description

def ensure_user_config():
    home = Path.home()
    config_dir = home / ".sectyra" / "codespace_data"
    source_dir = Path(__file__).parent / "codespace_data"
    if not config_dir.exists():
        if not source_dir.exists():
            raise FileNotFoundError(f"Source config directory not found: {source_dir}")
        shutil.copytree(source_dir, config_dir)
        print(Fore.YELLOW + f"[+] Initial configuration copied to {config_dir}" + Style.RESET_ALL)
    return config_dir

def main():
    ensure_user_config()
    description = create_description_with_banner()

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    parser_build = subparsers.add_parser("build", help="Build the Docker image")
    parser_build.add_argument("--tag", required=True, help="Docker image tag")
    parser_build.add_argument("--dockerfile-dir", required=True, help="Path to Dockerfile")

    parser_upload = subparsers.add_parser("upload", help="Upload the Docker image")
    parser_upload.add_argument("--tag", required=True, help="Docker image tag")
    parser_upload.add_argument("--registry", required=True, help="Registry URL",choices=["ghcr","dockerhub"])

    parser_start = subparsers.add_parser("start", help="Start the codespace")

    args = parser.parse_args()

    if args.command == "build":
        print(f"{Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}Building Docker image with tag{Style.RESET_ALL}: {Fore.GREEN}{args.tag}{Style.RESET_ALL} and Dockerfile: {Fore.GREEN}{args.dockerfile_dir}{Style.RESET_ALL}...\n")
        build_docker_image(dockerfile_dir=args.dockerfile_dir, image_name=args.tag)
    elif args.command == "upload":
        print(f"{Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}Uploading Docker image with tag{Style.RESET_ALL}: {Fore.GREEN}{args.tag}{Style.RESET_ALL} to registry: {Fore.GREEN}{args.registry}{Style.RESET_ALL}...\n")
        upload_image(image_name=args.tag, target=args.registry)
    elif args.command == "start":
        print(f"{Fore.YELLOW}[+]{Style.RESET_ALL} {Fore.WHITE}Starting codespace...{Style.RESET_ALL}\n")
        start_codespace()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

