# Simple File Integrity Monitor (FIM) Daemon

Hi! This is a simple Python script I created for my OS  practice. It works as a basic File Integrity Monitor (FIM) that runs in the background like a daemon to watch a specific file and check if someone modified it.

If any change happens, the script detects it and asks you if you want to accept the changes or rollback.

## Features
- GUI File Picker to select any file easily.
- Keeps watching the file in a loop (Daemon style).
- Restore the original file from backup folder (`./secure_backups`).
- Save logs in a simple text file (`fim_log.txt`).

## Requirements
- Python 3.x
- macOS, Linux or Windows 

## How to Run

1. Open your terminal in the project folder.
2. Run the script:
   ```bash
   python3 fim_daemon.py