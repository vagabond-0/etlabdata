from django.shortcuts import render
from django.http import HttpResponse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import os
import time

def run_selenium_script():
    download_dir = os.path.join(os.getcwd(), "downloads")
    chrome_options = webdriver.ChromeOptions()
    chrome_prefs = {
        "download.default_directory": download_dir,  
        "download.prompt_for_download": False, 
        "profile.default_content_settings.popups": 0,  
        "directory_upgrade": True
    }
    chrome_options.add_experimental_option("prefs", chrome_prefs)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    driver1 = webdriver.Chrome(options=chrome_options, service=ChromeService(ChromeDriverManager().install()))
    base_url = "https://tkmce.etlab.in/"
    driver1.get(base_url)

    time.sleep(5)
    
    login_form = WebDriverWait(driver1, 10).until(
        EC.presence_of_element_located((By.ID, "LoginForm_username"))
    ).send_keys("220904")
    password_form = driver1.find_element(By.ID, "LoginForm_password").send_keys("Abhijith@2005" + Keys.ENTER)

    time.sleep(5)
    
    driver1.get(base_url + "student/timetable/")
    time.sleep(5)
    icon_download = driver1.find_element(By.CLASS_NAME, "icon-download").click()
    time.sleep(5)

    dropdowntt = Select(driver1.find_element(By.XPATH, "/html/body/div[1]/div[4]/div[3]/div[3]/div/div[2]/form/div[2]/select"))
    dropdowntt.select_by_visible_text("Excel (CSV)")
    time.sleep(5)
    download_tt = driver1.find_element(By.XPATH, "/html/body/div[1]/div[4]/div[3]/div[3]/div/div[2]/form/div[3]/button").click()
    time.sleep(5)

    driver1.get(base_url + "ktuacademics/student/attendance/")
    time.sleep(3)
    attendance_select = driver1.find_element(By.XPATH, "/html/body/div[1]/div[4]/div[3]/div[3]/div/div/div[2]/ul/li[4]/a").click()
    time.sleep(3)
    export_attendance = driver1.find_element(By.XPATH, "/html/body/div[1]/div[4]/div[3]/div[3]/div/div/div[1]/div/a").click()
    time.sleep(3)
    dropdown_attend = Select(driver1.find_element(By.XPATH, "/html/body/div[1]/div[4]/div[3]/div[3]/div/div/div[2]/div[1]/form/div[2]/select"))
    time.sleep(2)
    dropdown_attend.select_by_visible_text("Excel (CSV)")
    time.sleep(2)
    download_attendance = driver1.find_element(By.XPATH, "/html/body/div[1]/div[4]/div[3]/div[3]/div/div/div[2]/div[1]/form/div[3]/button").click()
    time.sleep(5)
    
    driver1.quit()

def index(request):
    try:
        run_selenium_script()
        return HttpResponse("Selenium script ran successfully!")
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")
