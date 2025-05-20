#!/usr/bin/env python
# coding: utf-8

# In[6]:
import os
import time
import zipfile
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

TRACK_FILE = "last_downloaded_bse.txt"


def get_dates_to_download(days_back=7):
    today = datetime.today().date()
    if os.path.exists(TRACK_FILE):
        with open(TRACK_FILE, "r") as f:
            last_date_str = f.read().strip()
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
        next_date = last_date + timedelta(days=1)
        if next_date <= today:
            return [next_date + timedelta(days=i) for i in range((today - next_date).days + 1)]
        else:
            return []
    else:
        return [today - timedelta(days=i) for i in range(days_back)]


def save_last_downloaded(date):
    with open(TRACK_FILE, "w") as f:
        f.write(date.strftime("%Y-%m-%d"))

def download_and_extract_zip(target_date, base_download_dir):
    tmp_zip_name = "rename.zip"
    expected_csv_name = 'REG1_IND' + target_date.strftime('%d%m%y') + '.csv'
    renamed_zip_name = f"reg1_ind_{target_date.strftime('%d%m%y')}.zip"
    zip_path = os.path.join(base_download_dir, tmp_zip_name)
    renamed_zip_path = os.path.join(base_download_dir, renamed_zip_name)
    csv_extract_dir = os.path.join(base_download_dir, "csv_files")
    os.makedirs(csv_extract_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": base_download_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://member.bseindia.com/")
        wait = WebDriverWait(driver, 20)

        driver.find_element(By.LINK_TEXT, "EQ").click()
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "COMMON"))).click()

        month_str = target_date.strftime("%b").upper() + '-' + target_date.strftime("%Y")
        day_str = target_date.strftime("%d-%m-%Y")

        try:
            wait.until(EC.element_to_be_clickable((By.LINK_TEXT, month_str))).click()
            wait.until(EC.element_to_be_clickable((By.LINK_TEXT, day_str))).click()
            checkbox_xpath = f"//a[text()='{expected_csv_name}']/preceding::input[1]"
            wait.until(EC.element_to_be_clickable((By.XPATH, checkbox_xpath))).click()
        except (TimeoutException, NoSuchElementException):
            print(f"❌ File or navigation not available for {target_date.strftime('%Y-%m-%d')}, skipping.")
            return False

        download_btn_selector = (By.CSS_SELECTOR, 'input[type="submit"][value="Download"]')
        for attempt in range(3):
            try:
                download_button = wait.until(EC.element_to_be_clickable(download_btn_selector))
                download_button.click()
                break
            except StaleElementReferenceException:
                if attempt == 2:
                    print(f"❌ Stale element error for {target_date.strftime('%Y-%m-%d')}, skipping.")
                    return False
                time.sleep(1)

        # Wait for download to complete
        waited_time = 0
        while not os.path.exists(zip_path) and waited_time < 60:
            time.sleep(1)
            waited_time += 1

        if os.path.exists(zip_path):
            os.rename(zip_path, renamed_zip_path)
            print(f"📦 ZIP downloaded and renamed: {renamed_zip_path}")
            try:
                with zipfile.ZipFile(renamed_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(csv_extract_dir)
                print(f"✅ Extracted to: {csv_extract_dir}")
                return True
            except zipfile.BadZipFile:
                print(f"⚠️ Bad zip file for {target_date.strftime('%Y-%m-%d')}")
                return False
        else:
            print(f"⏳ Download timed out or failed for {target_date.strftime('%Y-%m-%d')}")
            return False
    finally:
        driver.quit()

if __name__ == "__main__":
    download_dir = os.path.join(os.getcwd(), "bse_data_files1")
    os.makedirs(download_dir, exist_ok=True)

    dates_to_download = get_dates_to_download(days_back=7)
    if not dates_to_download:
        print("✅ No new files to download.")
    else:
        for date in dates_to_download:
            success = download_and_extract_zip(date, download_dir)
            if success:
                save_last_downloaded(date)

