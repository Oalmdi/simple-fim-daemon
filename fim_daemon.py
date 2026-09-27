import os
import time
import hashlib
import shutil
import stat
import platform
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import filedialog


BACKUP_DIR = "./secure_backups"
LOG_FILE = "fim_log.txt"
POLL_INTERVAL = 2  

def calculate_hash(file_path):
    """Calculate SHA-256 hash to verify file integrity."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None

def safe_copy(src, dst):
    """Safely copies a file by removing write protection if needed."""
    try:
        if os.path.exists(dst):
            if platform.system() == "Windows":
                os.chmod(dst, stat.S_IWRITE)
            else:
                os.chmod(dst, stat.S_IWUSR | stat.S_IRUSR)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"[!] File Copy Error: {e}")
        return False

def close_editor_process(file_name):
    """Forcefully closes any open text editor / app accessing the modified file."""
    os_type = platform.system()
    try:
        if os_type == "Darwin":  # macOS
            
            subprocess.run(["pkill", "-x", "TextEdit"], stderr=subprocess.DEVNULL)
        elif os_type == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "notepad.exe"], stderr=subprocess.DEVNULL)
        elif os_type == "Linux":
            subprocess.run(["pkill", "-f", file_name], stderr=subprocess.DEVNULL)
    except Exception:
        pass

def write_to_log_txt(file_name, status, old_hash, new_hash, last_mod_time, current_mod_time):
    """Appends full detailed change logs into fim_log.txt."""
    log_entry = f"""--------------------------------------------------
[EVENT LOG] Date/Time: {current_mod_time}
Monitored File   : {file_name}
Action Status    : {status}
Previous Modified: {last_mod_time}
Current Modified : {current_mod_time}
Previous Hash    : {old_hash}
Current Hash     : {new_hash if new_hash else 'DELETED'}
--------------------------------------------------\n
"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def select_file_via_gui():
    """Open a minimal GUI file picker to select target file."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    file_path = filedialog.askopenfilename(title="Select File to Monitor")
    root.destroy()
    return file_path


if __name__ == "__main__":
    print("=== File Integrity Monitor Daemon ===")
    
    # User selects target file via GUI prompt
    selected_file = select_file_via_gui()
    
    if not selected_file or not os.path.exists(selected_file):
        print("[!] No file selected. Exiting.")
        exit(0)

    file_name = os.path.basename(selected_file)
    print(f"[*] FIM Daemon Started. Monitoring: {file_name}")

    #  Create backup directory & initial backup copy
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_file = os.path.join(BACKUP_DIR, file_name)
    safe_copy(selected_file, backup_file)

    #  Set initial baseline hash and timestamp
    baseline_hash = calculate_hash(selected_file)
    last_mod_time = datetime.fromtimestamp(os.path.getmtime(selected_file)).strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"[*] Initial Baseline Set. Log File: {LOG_FILE}")
    print("[*] Monitoring active... (Press Ctrl+C to exit)\n")

    #  Continuous Monitoring Loop (Daemon Behavior)
    try:
        while True:
            time.sleep(POLL_INTERVAL)
            current_hash = calculate_hash(selected_file)

            # Detect modifications or deletions
            if current_hash and current_hash != baseline_hash:
                current_mod_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"\n[ALERT {current_mod_time}] Change detected in '{file_name}'!")

                # Prompt user for authorization decision
                response = input("--> Approve this modification? (y/n): ").strip().lower()

                if response == 'y':
                    #  Save new details
                    write_to_log_txt(file_name, "APPROVED", baseline_hash, current_hash, last_mod_time, current_mod_time)
                    
                    #  Update baseline & backup
                    baseline_hash = current_hash
                    last_mod_time = current_mod_time
                    safe_copy(selected_file, backup_file)
                    
                    print(f" Change APPROVED. Log saved to '{LOG_FILE}'.\n")
                else:
                    #  Close application/editor displaying the file
                    close_editor_process(file_name)
                    
                    #  Log rejected modification
                    write_to_log_txt(file_name, "BLOCKED & REVERTED", baseline_hash, current_hash, last_mod_time, current_mod_time)
                    
                    #  Revert file immediately
                    safe_copy(backup_file, selected_file)
                    
                    print(f" Change BLOCKED & CLOSED. File reverted to original copy.\n")
                    
                    # Refresh hash after rollback
                    baseline_hash = calculate_hash(selected_file)

    except KeyboardInterrupt:
        print("\n[*] FIM Daemon stopped by user.")