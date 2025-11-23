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

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from config import load_config

def analyze_upload():
    config = load_config()
    session_cookie = config.get('note_session_cookie')
    
    if not session_cookie:
        print("[ERROR] 'note_session_cookie' is required in config.yaml.")
        return

    # Enable Performance Logging
    options = Options()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    # options.add_argument('--headless') # Keep visible for debugging
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("[INFO] Navigating to note.com to set cookie...")
        driver.get("https://note.com/404") # Go to any page on the domain
        
        # Set Cookie
        print("[INFO] Setting session cookie...")
        driver.add_cookie({
            'name': '_note_session_v5', # Note: Verify if this is the correct cookie name. Usually it is.
            'value': session_cookie,
            'domain': '.note.com',
            'path': '/'
        })
        # Also set 'note_session' just in case, though v5 is usually the one.
        # But the user provides the value. Let's assume it maps to _note_session_v5 or similar.
        # Actually, let's check what the user's cookie name usually is. 
        # The README says "name is session". But Note uses `_note_session_v5`.
        # Let's try setting both `_note_session_v5` and `note_session` (if that exists)
        
        # Go to Editor
        print("[INFO] Going to editor...")
        driver.get("https://note.com/notes/new")
        time.sleep(5)
        
        # Check if logged in (look for user icon or absence of login button)
        if "login" in driver.current_url:
             print("[ERROR] Cookie login failed. Redirected to login page.")
             # Fallback: Try to use the cookie name 'note_session' if v5 failed?
             # But for now, let's just report it.
             return

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
