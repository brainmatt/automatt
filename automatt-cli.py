import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"
import time
import sys
import asyncio
import pprint
import json
import argparse
# this is just to the alsa errors during init of speech-recognition
import sounddevice
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import importlib
import readkeys
import keyboard

# you may want/need to adjust the chrome path on windows
chrome_windows_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"

window_w, window_h = 1920, 1080
autmatt_model_provider_config = "./conf/automatt-model-provider.json"
default_model = "gemini-2.0-flash"
default_provider = "google"
default_browser = "chrome"

# cmdline args
parser = argparse.ArgumentParser()
parser.add_argument("-list", help="List configured model provider", action="store_true")
parser.add_argument("-listautologin", help="Lists thhe configured autologin-hooks in the ./hooks directory", action="store_true")
parser.add_argument("-run", help="Run automatt", action="store_true")
parser.add_argument("-provider", help="Model provider. Can be 'google', 'llmhub' or 'ollama'. 'google' by default")
parser.add_argument("-model", help="Model name. 'gemini-2.0-flash' by default.")
parser.add_argument("-baseurl", help="API base-url for the selected Model. empty by default.")
parser.add_argument("-autologin", help="Name of an existing auto-login-hook in the ./hooks directory. Performs an automatic login to a specific url before running the task.")
parser.add_argument("-browser", help="Choose which browser to use - 'chrome' or 'chromonium' are supported. 'chrome' by default.")


args = parser.parse_args()
if args.list:
    with open(autmatt_model_provider_config, 'r') as file:
        autmatt_model_provider_config_json = json.load(file)

    automatt_model_provider_arr = []
    for automatt_model_provider in autmatt_model_provider_config_json['model_provider']:
        print(automatt_model_provider['name'] + ";" + automatt_model_provider['model_name'] + ";" + automatt_model_provider['base_url'])
    sys.exit(0)

if args.listautologin:
    autologin_hooks_arr = os.listdir("./hooks")
    for hook in autologin_hooks_arr:
        if hook == "__init__.py":
            continue
        hook = hook.replace(".py", "")
        print(hook)
    sys.exit(0)

if args.run:
    print("Evaluating cmdline arguments ...")

if not args.provider:
    automatt_provider = default_provider
else:
    automatt_provider = args.provider

if not args.model:
    automatt_model = default_model
else:
    automatt_model = args.model

if not args.baseurl:
    automatt_baseurl = default_model
else:
    automatt_baseurl = args.baseurl

# browser
if args.browser:
    if args.browser == "chrome" or args.browser == "chromonium":
        default_browser = args.browser
    else:
        print("NOTICE: -browser can be set to 'chrome' or 'chomonium'")
        sys.exit(1)

# autologin
automatt_autologin_hook = ""
if args.autologin:
    automatt_autologin_hook = args.autologin


# as in json config ?
with open(autmatt_model_provider_config, 'r') as file:
    autmatt_model_provider_config_json = json.load(file)

inconfig = False
automatt_model_provider_arr = []
for automatt_model_provider in autmatt_model_provider_config_json['model_provider']:
    if automatt_model in automatt_model_provider['model_name'] and automatt_provider in automatt_model_provider['name']:
        print("NOTICE: Found model and provider in config")
        inconfig = True

if not inconfig:
    print("ERROR: model and/or provider not configured in " + autmatt_model_provider_config)
    print("NOTICE: Please configure in in this json file before using it.")
    sys.exit(0)


# check api-keys
if automatt_provider == "google":
    api_key_google = os.getenv('GOOGLE_API_KEY', '')
    if not api_key_google:
        raise ValueError('GOOGLE_API_KEY is not set')

if automatt_provider == "llmhub" or automatt_provider == "ollama":
    api_key_openai = os.getenv('OPENAI_API_KEY', '')
    if not api_key_openai:
        raise ValueError('OPENAI_API_KEY is not set')

# summary before starting
if not args.run:
    print("ERROR: Please use the '-run' parameter.")
    sys.exit(1)

if args.run:
    print("Starting AutoMatt")
    print("provider: " + automatt_provider)
    print("model " + automatt_model)

# late imports since they take some time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from browser_use import Agent, Browser, BrowserConfig
from browser_use.agent.views import AgentHistoryList

from browser_use.browser.context import (
    BrowserContextConfig,
    BrowserContextWindowSize,
)

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import (
    BrowserContext,
    BrowserContextConfig,
    BrowserContextWindowSize,
)

import speech_recognition as sr

# setup browser globally
browser_config = BrowserConfig(
    headless=False,
    disable_security=True,
    extra_chromium_args=[f"--window-size={window_w},{window_h}"],
    chrome_instance_path="/usr/bin/google-chrome",
    keep_alive=True,
)
browser = Browser(config=browser_config)

context_config = BrowserContextConfig(
    trace_path="./tmp/traces",
    save_recording_path="./tmp/record_videos",
    no_viewport=True,
    browser_window_size=BrowserContextWindowSize(width=window_w, height=window_h),
)
browser_context = BrowserContext(browser=browser, config=context_config)

async def run_agent(task: str, max_steps: int = 20):
    global automatt_provider
    global automatt_model
    global automatt_baseurl
    if automatt_provider == "google":
        llm = ChatGoogleGenerativeAI(
            model=automatt_model,
            temperature=0,
        )
    if automatt_provider == "llmhub":
        llm = ChatOpenAI(
            model=automatt_model,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            base_url=automatt_baseurl
        )
    if automatt_provider == "ollama":
        llm = ChatOpenAI(
            model=automatt_model,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            base_url=automatt_baseurl
        )

    print("NOTICE: Using provider/model: " + automatt_provider + " - " + automatt_model + " - base-url (if configured): " + automatt_baseurl)

    agent = Agent(
        task=task,
        llm=llm,
        #browser=browser,
        browser_context=browser_context,
        use_vision=True
    )

    # autologin hook
    if len(automatt_autologin_hook):
        if os.path.isfile("./hooks/" + automatt_autologin_hook + ".py"):
            print("NOTICE: Detected and running autologin hook " + automatt_autologin_hook)
            auto_login_hook_module = importlib.import_module("hooks." + automatt_autologin_hook, package=None)
            print("NOTICE: imported module")
            page = await browser_context.get_current_page()
            print("NOTICE: get page")
            print(page)
            print("NOTICE: before running it")
            await auto_login_hook_module.autologin(page)
            print("NOTICE: after running it")
            await asyncio.sleep(5)
            print("NOTICE: Finished autologin hook ")

    history: AgentHistoryList = await agent.run(max_steps=max_steps)

    print("Final Result:")
    pprint.pp(history.final_result(), indent=4)

    print("\nErrors:")
    pprint.pp(history.errors(), indent=4)

    # e.g. xPaths the model clicked on
    print("\nModel Outputs:")
    pprint.pp(history.model_actions(), indent=4)

    print("\nThoughts:")
    pprint.pp(history.model_thoughts(), indent=4)



async def mainloop():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    while True:

        # linux using readkeys / windows using keyboard which sadly requires root privs on linux
        if os.name == "nt":
            print("-> click '^' twice (with a short pause) to start recording :)")
            while True:
                if keyboard.is_pressed("^"):
                    break
                time.sleep(1)
        else:
            while True:
                print("-> click '^' twice to start recording :)")
                key = readkeys.getkey()  # get a single keypress
                #print(key)
                if key == '^':
                    break
                time.sleep(1)


        with microphone as source:
            print("\nListening for voice command...")
            recognizer.adjust_for_ambient_noise(source) # Optional: Reduce noise sensitivity
            recognizer.energy_threshold = 400
            audio = recognizer.listen(source, phrase_time_limit=30) # Limit listening time to prevent long pauses

        try:
            print("Recognizing...")
            task = recognizer.recognize_google(audio)
            print(f"Speech Recognition (Google SR) understood: '{task}'")

            await run_agent(task, 20)


        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Speech Recognition service; {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

asyncio.run(mainloop())




