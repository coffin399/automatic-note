import requests
import json
import re
import os

class NoteUploader:
    def __init__(self, session_cookie=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            # Initial headers for login (Origin/Referer might need to be note.com for login?)
            # The reference uses editor.note.com for everything, let's try that.
            response = self.session.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            # Debug: Print all cookies
            print(f"[DEBUG] Cookies after login: {self.session.cookies.get_dict()}")
            
            # Verify XSRF-TOKEN
            if "XSRF-TOKEN" in self.session.cookies:
                print("[DEBUG] XSRF-TOKEN found.")
            else:
                print("[WARN] XSRF-TOKEN not found in cookies.")

            # Check success by response content (if 'data' exists)
            data = response.json()
            if 'data' in data and 'email_confirmed_flag' in data['data']:
                print("[SUCCESS] Login successful (User data received).")
                return True
            else:
                print("[ERROR] Login response did not contain expected user data.")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Login failed: {e}")
            return False

        paragraphs = html.split('\n\n')
        html = '\n'.join([f'<p>{p}</p>' if not p.strip().startswith('<') else p for p in paragraphs])
        
        return html
    pass

if __name__ == "__main__":
    # Mock test
    pass
