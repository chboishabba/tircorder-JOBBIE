import subprocess
import sys
import json

def save_user_preferences(terminal):
    with open("userprefs.json", "w") as file:
        json.dump({"terminal": terminal}, file)

def load_user_preferences():
    try:
        with open("userprefs.json", "r") as file:
            prefs = json.load(file)
            return prefs["terminal"]
    except (FileNotFoundError, KeyError):
        return None

def select_terminal():
    terminals = {
        "1": "gnome-terminal --",
        "2": "xterm -e",
        "3": "konsole -e",
        "4": "xfce4-terminal -e",
        "5": "lxterminal -e",
        "6": "terminator -e",
        "7": "tilix -e",
        "8": "alacritty -e",
        "9": "guake -e",
        "10": "termite -e"
    }
    print("Select your preferred terminal emulator (enter the number):")
    for key, value in terminals.items():
        print(f"{key}: {value.split(' ')[0]}")
    choice = input("Choice (1-10): ")
    terminal = terminals.get(choice, "gnome-terminal --")
    save_user_preferences(terminal)
    return terminal

def check_for_updates():
    print("Checking for updates...")
    subprocess.run(["git", "pull"], check=True)

def check_install_requirements():
    print("Checking and installing requirements...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

def main_menu():
    return input("Choose an option:\n0. Run Server\n1. Run Client\n2. Run Both\nEnter choice (0, 1, 2): ")

def run_server(terminal_cmd):
    print("Starting server...")
    subprocess.Popen(terminal_cmd.split() + ["python", "run j_servski-11-05-24-9.py"])

def run_client(terminal_cmd):
    print("Starting client...")
    subprocess.Popen(terminal_cmd.split() + ["python", "jobbie_gpt_CLIENT_05-10-2024.py"])

if __name__ == "__main__":
    terminal_cmd = load_user_preferences()
    if not terminal_cmd:
        terminal_cmd = select_terminal()

    check_for_updates()
    check_install_requirements()
    
    choice = main_menu()
    if choice == "0":
        run_server(terminal_cmd)
    elif choice == "1":
        run_client(terminal_cmd)
    elif choice == "2":
        print("Running both server and client in separate instances.")
        run_server(terminal_cmd)
        run_client(terminal_cmd)
    else:
        print("Invalid choice. Exiting...")

