import os
import time
import sys
import json
import pprint
import argparse
import speech_recognition as sr
import tkinter as tk
import tkinter.scrolledtext as scrolledtext
from tkinter import ttk
from tkinter import messagebox
from tkinter import *

autmatt_model_provider_config = "./conf/automatt-model-provider.json"
automatt_server_log = "./logs/automatt-llm-server.log"
automatt_json_task = "./tasks/task.json"


def record_and_transcribe():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        print("\nListening for voice command...")
        recognizer.adjust_for_ambient_noise(source) # Optional: Reduce noise sensitivity
        recognizer.energy_threshold = 200
        audio = recognizer.listen(source) # Limit listening time to prevent long pauses

    try:
        print("Recognizing...")
        # Use SpeechRecognition to get text from audio (using default system recognizer - can be changed)
        task = recognizer.recognize_google(audio) # Using Google Speech Recognition
        print(f"Speech Recognition (Google SR) understood: '{task}'")
        return task


    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Speech Recognition service; {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



def record_task():
    task_field.delete("1.0", tk.END)  # Clear existing text
    task = record_and_transcribe()
    if task:
        task_field.insert(tk.END, task)
    run_button.config(state=tk.NORMAL) # Enable the Run button

def run_task():
    global browser
    global combo_autologin
    global model_provider_combo
    use_browser = browser.get()
    print("Starting task with " + use_browser)
    use_model_provider = model_provider_combo.get()
    print("Starting task with " + use_model_provider)
    use_auto_login = combo_autologin.get()
    print("Starting task with " + use_auto_login)
    task = task_field.get("1.0",tk.END)
    task = task.replace("'", "TICKMARKER")
    print("Starting task " + task)
    use_model_provider_arr = use_model_provider.split(";")
    use_provider = use_model_provider_arr[0]
    use_model = use_model_provider_arr[1]
    use_baseurl = use_model_provider_arr[2]
    # empty prompt
    if len(task) < 2:
        messagebox.showinfo(
            title="Empty Prompt!",
            message=f"EmptyNot starting task."
        )
        return

    json_task = {
      "task": [
        {
            "provider": use_provider,
            "model": use_model,
            "browser": use_browser,
            "autologin": use_auto_login,
            "baseurl": use_baseurl,
            "prompt": task
        }
      ]
    }

    json_task = str(json_task).replace("'", '\"')
    json_task = str(json_task).replace("TICKMARKER", "'")

    print(json_task)
    logs_field.delete("1.0", tk.END) # Clear existing text
    if task:
        f = open(automatt_json_task, "w")
        f.write(str(json_task))
        f.close()
        logs_field.insert(tk.END, task)


def quit_app():
    root.destroy()


def start_server():
    print("Starting the AutoMatt LLM Server")
    if os.name == 'nt':
        llm_server_cmdline = "powershell.exe .\\automatt-llm-server-background.ps1"
    else:
        llm_server_cmdline = "./automatt-llm-server-background"

    als = os.system(llm_server_cmdline)
    print(als)
    status_label.config(bg="green")
    stop_button.config(state=tk.NORMAL)
    start_button.config(state=tk.DISABLED)


def stop_server():
    print("Stopping the AutoMatt LLM Server")
    if os.name == 'nt':
        llm_server_cmdline = "powershell.exe .\\automatt-llm-server-background-stop.ps1"
    else:
        llm_server_cmdline = "./automatt-llm-server-background-stop"

    als = os.system(llm_server_cmdline)
    print(als)
    status_label.config(bg="red")
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)


def refresh_logs():
    global logs_field
    f = open(automatt_server_log, "r")
    logs = f.read()
    #print(logs)
    f.close()
    logs_field.delete("1.0", tk.END)
    logs_field.insert(tk.END, logs)
    logs_field.yview_moveto("1.0")
    print("Logs refreshed!") # Example action for now


def refresh_logs_auto():
    global logs_field
    if autorefresh == 1:
        f = open(automatt_server_log, "r")
        logs = f.read()
        f.close()
        logs_field.delete("1.0", tk.END)
        logs_field.insert(tk.END, logs)
        logs_field.yview_moveto("1.0")
        #print("Logs refreshed!") # Example action for now

    root.after(2000, refresh_logs_auto) # every second...


def truncate_logs():
    f = open(automatt_server_log, "w")
    f.truncate()
    f.close()
    logs = ""
    logs_field.delete("1.0", tk.END)
    logs_field.insert(tk.END, logs)
    logs_field.yview_moveto("1.0")
    print("Logs cleared!") # Example action for now

def clear_tasks():
    f = open(automatt_json_task, "w")
    f.truncate()
    f.close()
    task_field.delete("1.0", tk.END)
    print("Prompt cleared!") # Example action for now


# Create the main window
root = tk.Tk()
root.title("Automatt - the AI controlled Browser Assistant")

# Left Frame for Task and Logs
left_frame = tk.Frame(root, bd=2, relief=tk.GROOVE)
left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew") # sticky to expand if window resized

# Record Button
record_button = tk.Button(left_frame, text="Record", command=record_task)
record_button.grid(row=0, column=0, padx=5, pady=5, sticky="nw")

# clear Tasks Button
clear_tasks_button = tk.Button(left_frame, text="Clear", command=clear_tasks)
clear_tasks_button.grid(row=1, column=0, padx=5, pady=5, sticky="nw")

# Run Button
run_button = tk.Button(left_frame, text="Run", command=run_task)
run_button.grid(row=2, column=0, padx=5, pady=5, sticky="nw")


# select model/provider
def model_changed(event):
    selection = model_provider_combo.get()
    messagebox.showinfo(
        title="LLM Model/Provider selected!",
        message=f"Selected: {selection}"
    )

# model select
with open(autmatt_model_provider_config, 'r') as file:
    autmatt_model_provider_config_json = json.load(file)

ui_select_option = []
for automatt_model_provider in autmatt_model_provider_config_json['model_provider']:
    ui_select_option.append(automatt_model_provider['name'] + ";" + automatt_model_provider['model_name'] + ";" + automatt_model_provider['base_url'])

model_provider = StringVar()
model_provider_combo = ttk.Combobox(left_frame, values=model_provider, width=50)
model_provider_combo.bind("<<ComboboxSelected>>", model_changed)
model_provider_combo['values'] = ui_select_option
model_provider_combo.current(0)
model_provider_combo.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="nw")


# Task Text Field (Scrollable)
task_field = scrolledtext.ScrolledText(left_frame, height=4, width=50) # using scrolledtext
task_field.insert(INSERT, "Click 'Record' to record a prompt\nThen click on 'Run' to start the agent\n")
task_field.insert(END, "Enjoy!")
task_field.grid(row=0, column=1, padx=5, pady=5, rowspan=3, sticky="nw")


sep4 = ttk.Separator(master=left_frame, orient=tk.HORIZONTAL)
sep4.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")


# Refresh Button (placed in right frame, under Start/Stop buttons)
refresh_button = tk.Button(left_frame, text="Refresh", command=refresh_logs)
refresh_button.grid(row=4, column=0, padx=5, pady=5, sticky="nw")

# Truncate Button (placed in right frame, under Start/Stop buttons)
truncate_button = tk.Button(left_frame, text="Clear", command=truncate_logs)
truncate_button.grid(row=5, column=0, padx=5, pady=5, sticky="nw") # Row 3, span 2 columns

# autorefresh logs
autorefresh = IntVar(root)
autorefresh.set(0)

def manageautorefresh():
    global autorefresh
    #print("in manage")
    #print(autorefresh)
    if autorefresh == 1:
        autorefresh = 0
        #print("off")
    else:
        autorefresh = 1
        #print("on")


autorefresh_log = ttk.Checkbutton(left_frame, text='Autorefresh',
	    command=manageautorefresh, variable=autorefresh,
	    onvalue=1, offvalue=0)
autorefresh_log.grid(row=6, column=0, padx=5, pady=5, sticky="nw") # Row 3, span 2 columns
#autorefresh_log.invoke()

# Logs Text Field (Scrollable)
logs_field = scrolledtext.ScrolledText(left_frame, height=7, width=50) # using scrolledtext
logs_field.insert(INSERT, "Here the log of the Agent will appear.\n")
logs_field.insert(END, "Hint: Set 'autorefresh' to not miss anything.")
logs_field.grid(row=4, column=1, rowspan=3, padx=5, pady=5, sticky="nw")


# Right Frame for Server Controls
right_frame = tk.Frame(root, bd=2, relief=tk.GROOVE) # adding border for visual separation
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# AutoMatt Server Label
server_label = tk.Label(right_frame, text="AutoMatt Server", font=("Helvetica", 10, "bold")) # bold font
server_label.grid(row=0, column=0, columnspan=2, pady=5) # centered on top

# Status Label
status_label = tk.Label(right_frame, text="Status", bg="red", width=10, anchor="center") # red background, centered text
status_label.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")

# Start Button
start_button = tk.Button(right_frame, text="Start", command=start_server)
start_button.grid(row=2, column=0, padx=5, pady=5, sticky="w")

# Stop Button
stop_button = tk.Button(right_frame, text="Stop", command=stop_server)
stop_button.grid(row=2, column=1, padx=5, pady=5, sticky="e")

# check pid file if it is running already
pidfile = "./logs/pid.log"
if os.path.isfile(pidfile):
    f = open(pidfile, "r")
    pid = f.read()
    if pid:
        print("automatt-llm-server running")
        status_label.config(bg="green")

    else:
        print("automatt-llm-server stopped")
        status_label.config(bg="red")


sep1 = ttk.Separator(master=right_frame, orient=tk.HORIZONTAL)
sep1.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

# autologin label
autologin_label = tk.Label(right_frame, font=("Helvetica", 10, "bold"), text="AutoLogin Hook")
autologin_label.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

# select autologin hook
def autologin_changed(event):
    global combo_autologin
    selection = combo_autologin.get()
    messagebox.showinfo(
        title="New Selection",
        message=f"{selection}"
    )
    print("NOTICE: Setup " + selection)

# autologin hook select
autologin_value = StringVar()
combo_autologin = ttk.Combobox(right_frame, values=autologin_value)
combo_autologin.bind("<<ComboboxSelected>>", autologin_changed)

# get values from os.listdir
hooks_in_dir_arr = []
hooks_in_dir_arr.append("None")
hooks_in_dir = os.listdir('./hooks')
for h in hooks_in_dir:
    if h == ".gitignore":
        continue
    if h == "__init__.py":
        continue
    if h == "__pycache__":
        continue
    h = str(h)
    h = h.replace(".py", "")
    h = h.replace("[", "")
    h = h.replace("]", "")
    h = h.replace("'", '"')
    hooks_in_dir_arr.append(h)

combo_autologin['values'] = hooks_in_dir_arr
combo_autologin.current(0)
combo_autologin.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="en")


sep2 = ttk.Separator(master=right_frame, orient=tk.HORIZONTAL)
sep2.grid(row=6, column=0, columnspan=2, pady=5, sticky="ew")


browser = StringVar(root)
def select_browser():
    global browser
    b = browser.get()
    if b == 'chrome':
        print("Setting Brwoser to Chrome")
    if b == 'chromium':
        print("Setting Browser to Chromium")



chrome = ttk.Radiobutton(right_frame, text='Chrome', variable=browser, command=select_browser, value='chrome')
chrome.grid(row=7, column=0, pady=5, sticky="ew")
chrome.invoke()

chromium = ttk.Radiobutton(right_frame, text='Chromium', variable=browser, command=select_browser, value='chromium')
chromium.grid(row=7, column=1, pady=5, sticky="ew")


sep3 = ttk.Separator(master=right_frame, orient=tk.HORIZONTAL)
sep3.grid(row=8, column=0, columnspan=2, pady=5, sticky="ew")


# Quit Button
quit_button = tk.Button(right_frame, text="Quit", command=quit_app)
quit_button.grid(row=9, column=1, padx=5, pady=5, sticky="es")


# Configure column and row weights for resizing
root.columnconfigure(0, weight=1) # Left frame expands horizontally
root.columnconfigure(1, weight=1) # Right frame expands horizontally
root.rowconfigure(0, weight=1)    # Main row expands vertically
left_frame.columnconfigure(1, weight=1) # Make column with text fields expand

refresh_logs_auto()
# Run the Tkinter event loop
root.mainloop()
