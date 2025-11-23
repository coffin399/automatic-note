import os
import sys
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from config import load_config

def analyze_upload():
    config = load_config()
    email = config.get('note_email')
    password = config.get('note_password')
    
    if not email or not password:
        print("[ERROR] Email and password required in config.yaml for this analysis.")
        return

    # Enable Performance Logging
    options = Options()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    # options.add_argument('--headless') # Run visible to see what happens
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("[INFO] Navigating to login page...")
        driver.get("https://note.com/login")
        
        # Login
        print("[INFO] Logging in...")
        try:
            # Try multiple selectors for email
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='login'], input[type='email']"))
            )
            email_input.send_keys(email)
            
            password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password']")
            password_input.send_keys(password)
            
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[data-type='primary'], button[type='submit']")
            submit_btn.click()
        except Exception as e:
            print(f"[ERROR] Login element not found: {e}")
            driver.save_screenshot("login_error.png")
            with open("login_error.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return

        # Wait for login to complete
        time.sleep(5)
        print("[INFO] Login submitted. Waiting...")
        
        # Go to Editor
        print("[INFO] Going to editor...")
        driver.get("https://note.com/notes/new")
        time.sleep(5)
        
        # Find file input
        image_path = os.path.abspath("eyecatch.png")
        if not os.path.exists(image_path):
            print("[ERROR] eyecatch.png not found")
            return

        print(f"[INFO] Attempting to upload {image_path}...")
        
        try:
            # Try to find any file input
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(image_path)
            print("[INFO] File sent to input. Waiting for network traffic...")
        except Exception as e:
            print(f"[ERROR] File input not found: {e}")
            driver.save_screenshot("editor_error.png")
            return
        
        time.sleep(10) # Wait for upload
        
        # Analyze Logs
        print("[INFO] Analyzing network logs...")
        logs = driver.get_log('performance')
        
        found = False
        for entry in logs:
            log = json.loads(entry['message'])['message']
            if log['method'] == 'Network.requestWillBeSent':
                request = log['params']['request']
                url = request['url']
                if 'upload' in url or 'file' in url or 'asset' in url or 'image' in url:
                    if request['method'] == 'POST':
                        print(f"\n[FOUND CANDIDATE URL]: {url}")
                        print(f"Headers: {json.dumps(request['headers'], indent=2)}")
                        found = True
                        
            if log['method'] == 'Network.responseReceived':
                 response = log['params']['response']
                 url = response['url']
                 if 'upload' in url or 'file' in url or 'asset' in url or 'image' in url:
                     print(f"[RESPONSE] {url} -> {response['status']}")

        if not found:
            print("[WARN] No obvious upload request found.")

    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_upload()
