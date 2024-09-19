from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import csv
from django.views.decorators.csrf import csrf_exempt
import json

def calculate_attendance(attended, total, threshold=75):
    percentage = (attended / total) * 100
    if percentage < threshold:
        additional_classes = 0
        new_attended = attended
        new_total = total
        while (new_attended / new_total) * 100 < threshold:
            new_attended += 1
            new_total += 1
            additional_classes += 1
        return {
            "current_attendance": f"{attended}/{total} ({percentage:.2f}%)",
            "classes_needed": additional_classes,
            "projected_attendance": f"{new_attended}/{new_total} ({(new_attended / new_total) * 100:.2f}%)",
            "type": "attend"
        }
    else:
        cut_classes = 0
        new_attended = attended
        new_total = total
        while (new_attended / new_total) * 100 > threshold:
            new_total += 1
            cut_classes += 1
        new_total -= 1
        return {
            "current_attendance": f"{attended}/{total} ({percentage:.2f}%)",
            "classes_needed": cut_classes -1,
            "projected_attendance": f"{new_attended}/{new_total} ({(new_attended / new_total) * 100:.2f}%)",
            "type": "cut"
        }



def run_selenium_script(username, password):
    download_dir = "/app/downloads"
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-software-rasterizer')
       # Add these new options
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-browser-side-navigation')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
       # Increase page load timeout
    options.page_load_strategy = 'none'
       
       # Initialize WebDriver with a longer timeout
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30) 
    

    
    
    base_url = "https://tkmce.etlab.in/"
    
 
    driver.get(base_url)
    time.sleep(5)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "LoginForm_username"))
    ).send_keys(username)
    driver.find_element(By.ID, "LoginForm_password").send_keys(password + Keys.ENTER)
    
    time.sleep(5)
    
   
    driver.get(base_url + "student/timetable/")
    time.sleep(5)
   
    driver.find_element(By.CLASS_NAME, "icon-download").click()
    time.sleep(5)
    
    table = driver.find_element(By.XPATH, "/html/body/div[1]/div[4]/div[3]/div[3]/div/div/div[2]/div[2]/table")
    time.sleep(5)
    
    rows = table.find_elements(By.TAG_NAME, "tr")
    timetable = {}
    
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if cells:
            day = cells[0].text  
            schedule = [cell.text for cell in cells[1:]] 
            timetable[day] = schedule

    driver.get(base_url + "ktuacademics/student/attendance/")
    time.sleep(3)
    
    driver.find_element(By.XPATH, "/html/body/div[1]/div[4]/div[3]/div[3]/div/div/div[2]/ul/li[4]/a").click()
    time.sleep(3)
    
    export_attendance = driver.find_element(By.XPATH, "/html/body/div[1]/div[4]/div[3]/div[3]/div/div/div[2]/div[2]/center/table")
    time.sleep(3)
    heading_row = export_attendance.find_element(By.TAG_NAME, "thead")  # Extract thead for the heading row
    heading_cells = heading_row.find_elements(By.TAG_NAME, "th")  # Extract all 'th' elements
    headings = [cell.text for cell in heading_cells]  # Extract text from each heading cell
    content_rows = export_attendance.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
    content = []
    
    for row in content_rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        content_values = [cell.text for cell in cells]
        content.append(content_values)
    
    attendance = {}
    for i in range(len(content[0])):
        attendance[headings[i]] = content[0][i]
    
    time.sleep(2)
    driver.quit()
    student_attendance={}
    #Calculate the attendence
    subject_columns = [col for col in headings if col.startswith(('22', '23', '24', '21', '20'))]
    for subject in subject_columns:
        if subject in attendance:
            attendance_string = attendance[subject]
            try:
                attended, total = map(int, attendance_string.split('(')[0].split('/'))
                result = calculate_attendance(attended, total)
                student_attendance[subject] = result
            except ValueError:
                student_attendance[subject] = {
                    "error": "Invalid format",
                    "current_attendance": attendance_string
                }
    attendance['attendence'] = student_attendance
    attendance["timatable"] = timetable
    return attendance


@csrf_exempt
def index(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            user = body.get('username')
            password = body.get('password')
            attendence=run_selenium_script(user,password)
            return JsonResponse(attendence)
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")
    else:
        return HttpResponse(f"an unsupported method")
