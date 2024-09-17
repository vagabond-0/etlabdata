from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import csv
from django.views.decorators.csrf import csrf_exempt
import json


def run_selenium_script(username, password):
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
    ).send_keys(username)
    password_form = driver1.find_element(By.ID, "LoginForm_password").send_keys(password + Keys.ENTER)

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

@csrf_exempt
def index(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            user = body.get('username')
            password = body.get('password')
            run_selenium_script(user,password)
            return HttpResponse("Selenium script ran successfully!")
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}")
    else:
        return HttpResponse(f"an unsupported method")
def getattendence(request):
    try:
        download_dir = os.path.join(os.getcwd(), "downloads")
        csv_file = None
        for file in os.listdir(download_dir):
            if file.startswith("Subjectwise") and file.endswith(".csv"):
                csv_file = os.path.join(download_dir, file)
                break

        if not csv_file:
            return HttpResponse("CSV file not found", status=404)

        attendance_data = []
        with open(csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            first_row = next(csv_reader)
            if "TKM College of Engineering" in first_row[0]:
                header = next(csv_reader)
            else:
                header = first_row

            for row in csv_reader:
                student_dict = {header[i]: row[i] for i in range(len(header))}
                attendance_data.append(student_dict)

        return JsonResponse(attendance_data, safe=False)
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")
def gettimetable(request):
    try:
        download_dir = os.path.join(os.getcwd(),"downloads")
        csv_file = os.path.join(download_dir,"Time Table.csv")

        if not os.path.exists(csv_file):
            return HttpResponse("CSV file not found", status=404)

        timetable = {}
        with open(csv_file,mode='r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  
            headers = next(csv_reader)  

            for row in csv_reader:
                day = row[0]  
                periods = {headers[i]: row[i] for i in range(1, len(row))}  
                timetable[day] = periods
        return JsonResponse(timetable, safe=False)   
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")

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

def get_attendance_improvement(request):
    try:
        download_dir = os.path.join(os.getcwd(), "downloads")
        csv_file = None
        for file in os.listdir(download_dir):
            if file.startswith("Subjectwise") and file.endswith(".csv"):
                csv_file = os.path.join(download_dir, file)
                break

        if not csv_file:
            return HttpResponse("CSV file not found", status=404)

        attendance_data = []
        with open(csv_file, mode='r') as file:
            csv_reader = csv.reader(file)
            first_row = next(csv_reader)
            if "TKM College of Engineering" in first_row[0]:
                header = next(csv_reader)
            else:
                header = first_row

            # Identify subject columns
            subject_columns = [col for col in header if col.startswith(('22', '23', '24', '21', '20'))]

            for row in csv_reader:
                student_dict = {header[i]: row[i] for i in range(len(header))}
                student_attendance = {}
                
                for subject in subject_columns:
                    if subject in student_dict:
                        attendance_string = student_dict[subject]
                        try:
                            attended, total = map(int, attendance_string.split('(')[0].split('/'))
                            result = calculate_attendance(attended, total)
                            student_attendance[subject] = result
                        except ValueError:
                            student_attendance[subject] = {
                                "error": "Invalid format",
                                "current_attendance": attendance_string
                            }

                student_dict['attendance'] = student_attendance
                attendance_data.append(student_dict)

        return JsonResponse(attendance_data, safe=False)
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")