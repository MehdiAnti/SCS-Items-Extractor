import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import zipfile
from datetime import datetime
import logging
import threading
import shutil
import sys
import re
import time

APP_PATH = os.path.join("data", "converter_pix.exe")
SCS_FILES_PATH = os.path.join("data", "scs_files.txt")

ATS_FILES = []
ETS2_FILES = []

LOG_FILENAME = 'log.txt'

if os.path.exists(LOG_FILENAME):
    os.remove(LOG_FILENAME)

logging.basicConfig(level=logging.INFO, filename=LOG_FILENAME,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Application started. Hi, here you can see application logs.")

if not os.path.exists(APP_PATH):
    logging.error("PIX 'converter_pix.exe' not found. Application will exit.")
    messagebox.showerror("Error", "PIX 'converter_pix.exe' not found. Application will exit.")
    sys.exit(1)

if not os.path.exists(SCS_FILES_PATH):
    logging.error("SCS files configuration 'scs_files.txt' not found. Application will exit.")
    messagebox.showerror("Error", "SCS files configuration 'scs_files.txt' not found. Application will exit.")
    sys.exit(1)

def load_scs_files():
    global ATS_FILES, ETS2_FILES
    try:
        with open(SCS_FILES_PATH, 'r') as file:
            content = file.read()

        sections = content.split('}')
        for section in sections:
            if 'ets2_entries:' in section:
                ets2_part = section.split('{')
                if len(ets2_part) > 1:
                    ets2_entries = ets2_part[1].strip().splitlines()
                    ETS2_FILES = [line.strip() for line in ets2_entries if line.strip()]
            elif 'ats_entries:' in section:
                ats_part = section.split('{')
                if len(ats_part) > 1:
                    ats_entries = ats_part[1].strip().splitlines()
                    ATS_FILES = [line.strip() for line in ats_entries if line.strip()]
    except Exception as e:
        logging.error(f"Failed to load SCS files: {str(e)}")

load_scs_files()

pattern_inventory = re.compile(r'^\s*steam_inventory_id\s*:', re.MULTILINE | re.IGNORECASE)
pattern_academy = re.compile(r'^\s*academy_reward\s*:', re.MULTILINE | re.IGNORECASE)

def get_temp_cleanup_folder():
    temp_folder = os.path.join(os.getenv('TEMP'), 'scs_cleanup_temp')
    os.makedirs(temp_folder, exist_ok=True)
    return temp_folder

def process_file(file_path, temp_folder):
    file_name = os.path.basename(file_path)
    try:
        if file_name == "def.scs":
            arguments = [
                '/def/desktop/',
                '/def/vehicle/truck/',
                '/def/vehicle/trailer_owned/',
                '/def/vehicle/addon_hookups/'
            ]
        else:
            arguments = [
                '/def/vehicle/truck/',
                '/def/vehicle/trailer_owned/'
            ]

        for arg in arguments:
            command = [APP_PATH, '-b', file_path, '-extract_d', arg, '-e', temp_folder]
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            process.communicate()
            if process.returncode != 0:
                logging.error(f"Error processing {file_name}")
            else:
                logging.info(f"{file_name} processed successfully.")

        matched_files = []

        for root, _, files in os.walk(temp_folder):
            for f in files:
                if f.endswith(('.sii', '.sui')):
                    full_path = os.path.join(root, f)
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as fh:
                            content = fh.read()
                            if pattern_inventory.search(content) or pattern_academy.search(content):
                                matched_files.append(full_path)
                    except Exception as e:
                        logging.warning(f"Failed to read {full_path}: {e}")

        for root, dirs, files in os.walk(temp_folder, topdown=False):
            for f in files:
                full_path = os.path.join(root, f)
                if full_path not in matched_files:
                    os.remove(full_path)
            for d in dirs:
                if not os.listdir(os.path.join(root, d)):
                    os.rmdir(os.path.join(root, d))

        return bool(matched_files)

    except Exception as e:
        logging.error(f"Exception processing {file_name}: {str(e)}")
        return False

def extract_game_version(folder_path, temp_folder):
    version_file_path = os.path.join(folder_path, "version.scs")
    if os.path.isfile(version_file_path):
        command = [APP_PATH, "-b", version_file_path, "-extract_d", "/", "-e", temp_folder]
        try:
            subprocess.run(command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            sui_file_path = os.path.join(temp_folder, "version.sii")
            if os.path.isfile(sui_file_path):
                with open(sui_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    match = re.search(r'version:\s*"([^"]*)"', content)
                    if match:
                        return match.group(1)
                os.remove(sui_file_path)
        except subprocess.CalledProcessError:
            logging.error(f"Error extracting version from {version_file_path}")
    return None

def zip_temp_folder(folder_path, temp_folder, game_version):
    game_type = "ets2" if "Euro Truck Simulator 2" in folder_path else "ats" if "American Truck Simulator" in folder_path else ""
    version_suffix = f"{game_version}" if game_version else ""
    timestamp = datetime.now().strftime("%m%d_%H%M%S")
    zip_file_path = os.path.join(folder_path, f'{game_type}_{version_suffix}_packed_{timestamp}.zip')
    zip_file_path = zip_file_path.replace('\\', '/')
    try:
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for dirpath, _, filenames in os.walk(temp_folder):
                for file in filenames:
                    file_path = os.path.join(dirpath, file)
                    zip_file.write(file_path, os.path.relpath(file_path, temp_folder))
        logging.info(f"Temporary folder zipped to: {zip_file_path}")
    except Exception as e:
        logging.error(f"Failed to zip temporary folder: {str(e)}")

def process_scs_files(folder_path, progress_var, progress_bar, file_list):
    if not os.path.exists(folder_path):
        messagebox.showerror("Error", "The specified folder does not exist.")
        return

    total_files = len(file_list)
    if total_files == 0:
        logging.error("No .scs files found for processing.")
        messagebox.showerror("Error", "No .scs files found for processing.")
        return

    all_successful = True
    start_time = datetime.now()

    temp_processing_folder = os.path.join(folder_path, "temp_proc")
    os.makedirs(temp_processing_folder, exist_ok=True)

    processed_files = []

    progress_bar.pack(fill=tk.X)

    for i, file in enumerate(file_list):
        file_path = os.path.join(folder_path, file)
        if os.path.exists(file_path):
            if process_file(file_path, temp_processing_folder):
                processed_files.append(file)
            else:
                all_successful = False
        else:
            logging.warning(f"File not found, skipping: {file}")

        progress_var.set((i + 1) / total_files * 50)
        progress_bar.update_idletasks()

    game_version = extract_game_version(folder_path, temp_processing_folder)

    if processed_files:
        try:
            zip_temp_folder(folder_path, temp_processing_folder, game_version)
        except Exception as e:
            logging.error(f"Zipping failed: {str(e)}")

    try:
        shutil.rmtree(temp_processing_folder)
    except Exception as e:
        logging.error(f"Failed to delete temp folders: {str(e)}")

    for i in range(15):
        progress_var.set(85 + i)
        progress_bar.update_idletasks()
        time.sleep(0.02)

    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"Processing completed in: {duration}")

    if processed_files:
        messagebox.showinfo("Info", "Processing completed!")
    else:
        messagebox.showinfo("Info", "No files were successfully processed.")

    progress_var.set(0)
    progress_bar.pack_forget()

def threaded_process(folder_path, file_list):
    process_scs_files(folder_path, progress_var, progress_bar, file_list)

def select_folder():
    folder_path = filedialog.askdirectory(title="Select the folder containing .scs files")
    if folder_path:
        logging.info(f"Folder selected: {folder_path}")
        progress_var.set(0)

        files_in_folder = [f for f in os.listdir(folder_path) if f.endswith('.scs')]
        if not files_in_folder:
            logging.error("No .scs files found in the selected path.")
            messagebox.showerror("Error", "No .scs files found in the selected path. Please select another path.")
            return

        if "Euro Truck Simulator 2" in folder_path:
            file_list = ETS2_FILES
        elif "American Truck Simulator" in folder_path:
            file_list = ATS_FILES
        else:
            messagebox.showerror("Error", "The selected folder does not contain valid SCS files.")
            return

        if not file_list:
            logging.error("No valid .scs files found for processing.")
            messagebox.showerror("Error", "No valid .scs files found for processing.")
            return

        threading.Thread(target=threaded_process, args=(folder_path, file_list)).start()

def on_closing():
    logging.info("Exit.")
    root.destroy()

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

root = tk.Tk()
root.title("SCS File Processor")
root.geometry("300x100")
root.resizable(False, False)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)

select_button = tk.Button(root, text="Select Folder", command=select_folder)
select_button.pack(pady=20)

root.protocol("WM_DELETE_WINDOW", on_closing)

center_window(root)
root.mainloop()
