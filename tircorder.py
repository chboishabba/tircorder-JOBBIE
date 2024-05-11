import subprocess
import sys
import os

def check_for_updates():
    try:
        print("Checking for updates...")
        subprocess.run(["git", "pull"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to update: {e}")
    else:
        print("Update check complete.")

def check_install_requirements():
    try:
        print("Checking and installing requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install required packages: {e}")
    else:
        print("Requirements are up to date.")

def main_menu():
    choice = input("Choose an option:\n0. Run Server\n1. Run Client\n2. Run Both\nEnter choice (0, 1, 2): ")
    return choice

def run_server():
    print("Starting server...")
    os.system("python run j_servski-11-05-24-9.py")

def run_client():
    print("Starting client...")
    os.system("python jobbie_gpt_CLIENT_05-10-2024.py")

if __name__ == "__main__":
    check_for_updates()
    check_install_requirements()
    
    choice = main_menu()
    if choice == "0":
        run_server()
    elif choice == "1":
        run_client()
    elif choice == "2":
        print("Running both server and client in separate instances.")
        # This part is a little tricky in a single script, especially for opening new terminal windows.
        # Here's a way to do it for Windows:
        os.system("start cmd /c python run j_servski-11-05-24-9.py")
        os.system("start cmd /c python jobbie_gpt_CLIENT_05-10-2024.py")
    else:
        print("Invalid choice. Exiting...")

