# coding: utf-8

import os
import time
import datetime
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

SAVE_DIR = "nse_data"
os.makedirs(SAVE_DIR, exist_ok=True)

def get_cookie_session():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://www.nseindia.com")
    print("🌐 Opened NSE home page to set cookies...")
    time.sleep(5)

    cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
    driver.quit()
    return cookies

def get_last_year_dates():
    today = datetime.date.today()
    return [today - datetime.timedelta(days=i) for i in range(1, 366)]  # yesterday to 365 days ago

def download_files():
    cookies = get_cookie_session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nseindia.com/all-reports",
        "Accept": "application/octet-stream",
        "Connection": "keep-alive",
    }

    dates = get_last_year_dates()
    success = 0

    for date in dates:
        date_str = date.strftime("%d%m%y")
        url = f"https://nsearchives.nseindia.com/content/cm/REG1_IND{date_str}.csv"
        file_path = os.path.join(SAVE_DIR, f"REG1_IND{date_str}.csv")

        if os.path.exists(file_path):
            print(f"⏩ Already exists: {file_path}")
            continue

        print(f"🔄 Fetching: {url}")
        try:
            response = requests.get(url, headers=headers, cookies=cookies, timeout=10)

            if response.status_code == 200 and response.content:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Saved: {file_path}")
                success += 1
            else:
                print(f"❌ Skipped: No content or 404 for {date_str} (Status: {response.status_code})")
        except requests.RequestException as e:
            print(f"❌ Error: {url} - {str(e)}")

    print(f"\n🎯 Downloaded {success} file(s) for the last 1 year.")

if __name__ == "__main__":
    download_files()
