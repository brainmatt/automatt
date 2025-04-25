import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"
import logging
logger = logging.getLogger('AutoMatt')
if os.name == 'nt':
    logging.basicConfig(filename='./logs/automatt-llm-server.log', encoding='cp1252', level=logging.DEBUG)
else:
    logging.basicConfig(filename='./logs/automatt-llm-server.log', encoding='utf-8', level=logging.DEBUG)
logger.info('Starting the AutoMatt-LLM Server')

import time
import sys
import json
import asyncio
import pprint
import importlib

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


# you may want/need to adjust the chrome path on windows
chrome_windows_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"

window_w, window_h = 1920, 1080
automatt_json_task = "./tasks/task.json"

async def run_agent(max_steps: int = 20):
    automatt_model_provider = ""
    automatt_model_name = ""
    automatt_browser_config = ""
    automatt_autologin_hook = ""
    automatt_model_base_url = ""


    task = ""
    with open(automatt_json_task, 'r') as file:
        automatt_json_task_json = json.load(file)
        for t in automatt_json_task_json['task']:
            automatt_model_provider = t['provider']
            automatt_model_name = t['model']
            automatt_browser_config = t['browser']
            automatt_autologin_hook = t['autologin']
            automatt_model_base_url = t['baseurl']
            task = t['prompt']

    if "None" in automatt_autologin_hook:
        automatt_autologin_hook = ""

    # truncate immediatly
    d = open(automatt_json_task, "w")
    d.truncate()
    d.close()

    # model + provider config
    if automatt_model_provider == "google":
        api_key_google = os.getenv('GOOGLE_API_KEY', '')
        if not api_key_google:
            raise ValueError('GOOGLE_API_KEY is not set')
            sys.exit(1)

    if automatt_model_provider == "llmhub":
        api_key_openai = os.getenv('OPENAI_API_KEY', '')
        if not api_key_openai:
            raise ValueError('OPENAI_API_KEY is not set')
            sys.exit(1)

    if automatt_model_provider == "ollama":
        api_key_openai = os.getenv('OPENAI_API_KEY', '')
        if not api_key_openai:
            print("Using local Ollama model provider with no API key.")
        else:
            print("Using local Ollama model provider with API key.")

    if automatt_model_provider == "google":
        llm = ChatGoogleGenerativeAI(
            model=automatt_model_name,
            temperature=0,
        )
    if automatt_model_provider == "llmhub":
        llm = ChatOpenAI(
            model=automatt_model_name,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            base_url=automatt_model_base_url
        )
    if automatt_model_provider == "ollama":
        llm = ChatOpenAI(
            model=automatt_model_name,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            base_url=automatt_model_base_url
        )
    logger.info("NOTICE: Using provider/model: " + automatt_model_provider + " - " + automatt_model_name)
    # end of model config

    # browser config
    # choose browser according to automatt_browser_config
    if automatt_browser_config == "chrome":
        # windows
        if os.name == 'nt':

            google_chrome_windows_path = ""
            google_chrome_windows_path1 = chrome_windows_path

            if os.path.isfile(google_chrome_windows_path1):
                google_chrome_windows_path = google_chrome_windows_path1

            browser_config = BrowserConfig(
                headless=False,
                disable_security=True,
                extra_chromium_args=[f"--window-size={window_w},{window_h}"],
                chrome_instance_path=google_chrome_windows_path,
                keep_alive=True,
            )

        else:

            # linux
            google_chrome_path1 = "/usr/bin/google-chrome"
            google_chrome_path2 = "/usr/bin/chrome"
            google_chrome_path = ""

            if os.path.isfile(google_chrome_path1):
                google_chrome_path = google_chrome_path1
            elif os.path.isfile(google_chrome_path2):
                google_chrome_path = google_chrome_path2

            browser_config = BrowserConfig(
                headless=False,
                disable_security=True,
                extra_chromium_args=[f"--window-size={window_w},{window_h}"],
                chrome_instance_path=google_chrome_path,
                keep_alive=True,
            )

    elif automatt_browser_config == "chromium":
        browser_config = BrowserConfig(
            headless=False,
            disable_security=True,
            extra_chromium_args=[f"--window-size={window_w},{window_h}"],
            keep_alive=True,
        )
    else:
        browser_config = BrowserConfig(
            headless=False,
            disable_security=True,
            extra_chromium_args=[f"--window-size={window_w},{window_h}"],
            keep_alive=True,
        )

    browser = Browser(config=browser_config)
    # end of preconfig

    # agent start
    async with await browser.new_context(
            config=BrowserContextConfig(
                trace_path="./tmp/traces",
                save_recording_path="./tmp/record_videos",
                no_viewport=False,
                browser_window_size=BrowserContextWindowSize(width=window_w, height=window_h),
            )
    ) as browser_context:

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
                logger.info("NOTICE: Detected and running autologin hook " + automatt_autologin_hook)
                auto_login_hook_module = importlib.import_module("hooks." + automatt_autologin_hook, package=None)
                logger.info("NOTICE: imported module")
                page = await browser_context.get_current_page()
                logger.info("NOTICE: get page")
                #print(page)
                logger.info("NOTICE: before running it")
                await auto_login_hook_module.autologin(page)
                logger.info("NOTICE: after running it")
                await asyncio.sleep(5)
                logger.info("NOTICE: Finished autologin hook ")

        # here the agent starts running
        history: AgentHistoryList = await agent.run(max_steps=max_steps)

        logger.info("Final Result:")
        #pprint.pp(history.final_result(), indent=4)
        logger.info(history.final_result())

        logger.info("\nErrors:")
        #pprint.pp(history.errors(), indent=4)
        logger.info(history.errors())

        # e.g. xPaths the model clicked on
        logger.info("\nModel Outputs:")
        #pprint.pp(history.model_actions(), indent=4)
        logger.info(history.model_actions())

        logger.info("\nThoughts:")
        #pprint.pp(history.model_thoughts(), indent=4)
        logger.info(history.model_thoughts())

        # strange that chromium browser closes automaically here in opposite to chrome
        # so we keep it open for the "Future" ;)
        #if automatt_browser_config == "chromium":
        #    print("NOTICE: Chromium browser detected .... keeping it open.")
        #    await asyncio.Future()

# here we go
while True:
    if os.path.isfile(automatt_json_task):
        f = open(automatt_json_task, "r")
        task = f.read()
        if task:
            logger.debug("Running task ...")
            asyncio.run(run_agent(20))
        else:
            f.close()

    time.sleep(1)



