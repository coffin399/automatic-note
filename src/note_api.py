import requests
import json
import markdown
import re

class NoteUploader:
    def __init__(self, session_cookie=None):
        self.cookies = {}
        if session_cookie:
            self.cookies["session"] = session_cookie
            
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }

    def login(self, email, password):
        """
        Logs in to Note.com and retrieves the session cookie.
        """
        print(f"[INFO] Logging in as {email}...")
        url = 'https://note.com/api/v1/sessions/sign_in'
        payload = {
            'login': email,
            'password': password
        }
        
        try:
            # Note: This might fail if CAPTCHA is triggered
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # Extract cookies
            if 'session' in response.cookies:
                self.cookies['session'] = response.cookies['session']
                print("[SUCCESS] Login successful. Session cookie retrieved.")
                return True
            else:
                print("[ERROR] Login failed. Session cookie not found in response.")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Login failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return False

    def markdown_to_html(self, markdown_text):
        """
        Converts Markdown to HTML suitable for Note.com.
        Note.com accepts simple HTML.
        """
        # Basic conversion
        html = markdown.markdown(markdown_text)
        # Note might need specific formatting, but standard HTML usually works for the body.
        # We might need to adjust headers or paragraphs if Note's editor behaves strictly.
        return html

    def create_article(self, title, body_markdown, status="draft"):
        """
        Creates a new article on Note.com.
        status: 'draft' or 'published' (default: 'draft')
        """
        if 'session' not in self.cookies:
            print("[ERROR] No session cookie available. Cannot upload.")
            return None

        print(f"[INFO] Uploading article: {title} (Status: {status})")
        
        body_html = self.markdown_to_html(body_markdown)
        
        url = 'https://note.com/api/v1/text_notes'
        
        payload = {
            'name': title,
            'body': body_html,
            'template_key': None
        }
        
        try:
            # 1. Create the note (Draft)
            response = requests.post(url, cookies=self.cookies, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            note_id = data['data']['id']
            note_key = data['data']['key']
            print(f"[INFO] Draft created. ID: {note_id}, Key: {note_key}")

            # 2. Update status if needed (though creating usually makes it a draft)
            # If we want to publish, we might need a separate call or parameter.
            # For now, we stick to draft as requested by user safety.
            if status == 'published':
                print("[WARN] Auto-publishing is risky. Keeping as draft for safety.")
            
            return f"https://note.com/notes/{note_key}"

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return None

if __name__ == "__main__":
    # Mock test
    pass
