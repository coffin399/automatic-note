import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from note_api import NoteUploader

def test_upload():
    config = load_config()
    
    # Initialize Uploader
    session_cookie = config.get('note_session_cookie')
    uploader = None
    
    if session_cookie and not session_cookie.startswith("YOUR_"):
        uploader = NoteUploader(session_cookie=session_cookie)
        print("[INFO] Using configured session cookie.")
    else:
        print("[INFO] Session cookie not found. Attempting auto-login...")
        email = config.get('note_email')
        password = config.get('note_password')
        
        if email and password:
            uploader = NoteUploader()
            if not uploader.login(email, password):
                print("[FATAL] Auto-login failed.")
                return
        else:
            print("[FATAL] No session cookie and no credentials provided.")
            return

import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from note_api import NoteUploader

def test_upload():
    config = load_config()
    
    # Initialize Uploader
    session_cookie = config.get('note_session_cookie')
    uploader = None
    
    if session_cookie and not session_cookie.startswith("YOUR_"):
        uploader = NoteUploader(session_cookie=session_cookie)
        print("[INFO] Using configured session cookie.")
    else:
        print("[INFO] Session cookie not found. Attempting auto-login...")
        email = config.get('note_email')
        password = config.get('note_password')
        
        if email and password:
            uploader = NoteUploader()
            if not uploader.login(email, password):
                print("[FATAL] Auto-login failed.")
                return
        else:
            print("[FATAL] No session cookie and no credentials provided.")
            return

    image_path = "eyecatch.png"
    if not os.path.exists(image_path):
        print("Image not found")
        return

    endpoints = [
        "https://note.com/api/v1/image_upload/note_eyecatch"
    ]
    
    base_headers = uploader.get_headers()
    base_headers['X-Requested-With'] = 'XMLHttpRequest'
    if 'Content-Type' in base_headers:
        del base_headers['Content-Type']

    # Only test the most likely header combination (Origin: note.com)
    headers = base_headers.copy()
    headers['Origin'] = 'https://note.com'
    headers['Referer'] = 'https://note.com/notes/new'

    keys_to_test = ['file', 'image', 'resource', 'eyecatch', 'data']

    for url in endpoints:
        print(f"Testing {url}...")
        
        for key in keys_to_test:
            try:
                with open(image_path, 'rb') as f:
                    f.seek(0)
                    files = {key: (os.path.basename(image_path), f, 'image/png')}
                    
                    print(f"  Testing key: '{key}' ...")
                    response = uploader.session.post(url, headers=headers, files=files)
                    
                    print(f"    Status: {response.status_code}")
                    if response.status_code in [200, 201]:
                        print(f"SUCCESS! Endpoint: {url} (Key: '{key}')")
                        print(f"Response: {response.text[:200]}")
                        return
                    elif response.status_code == 403:
                        print(f"    Headers: {response.headers}")
                        
            except Exception as e:
                print(f"Failed with key {key}: {e}")

if __name__ == "__main__":
    test_upload()
