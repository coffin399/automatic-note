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
        "https://note.com/api/v1/upload_image",
        "https://note.com/api/v1/files"
    ]
    
    headers = uploader.get_headers()
    # Remove Content-Type if it exists, requests adds it for files
    if 'Content-Type' in headers:
        del headers['Content-Type']

    for url in endpoints:
        print(f"Testing {url}...")
        try:
            with open(image_path, 'rb') as f:
                # Try 'file' key as per article
                files = {'file': (os.path.basename(image_path), f, 'image/png')}
                
                # Try without extra data first
                response = uploader.session.post(url, headers=headers, files=files)
                print(f"  Files only -> Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"SUCCESS! Response: {response.text[:200]}")
                    return
                
                # Reset file pointer
                f.seek(0)
                
                # Try with data
                data = {'type': 'Note::Image'}
                response = uploader.session.post(url, headers=headers, files=files, data=data)
                print(f"  With data -> Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"SUCCESS! Response: {response.text[:200]}")
                    return

        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_upload()
