import requests
import json
import markdown
import re

class NoteUploader:
    def __init__(self, session_cookie=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        })
        
        if session_cookie:
            self.session.cookies.set("session", session_cookie, domain=".note.com")

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
        
        # Add headers to mimic browser
        headers = {
            'Origin': 'https://note.com',
            'Referer': 'https://note.com/login',
            'X-Requested-With': 'XMLHttpRequest'
        }

        try:
            response = self.session.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Debug: Print all cookies
            print(f"[DEBUG] Cookies after login: {self.session.cookies.get_dict()}")

            # Check success by response content (if 'data' exists)
            data = response.json()
            if 'data' in data and 'email_confirmed_flag' in data['data']:
                print("[SUCCESS] Login successful (User data received).")
                # We assume cookies are handled by session
                return True
            else:
                print("[ERROR] Login response did not contain expected user data.")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Login failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return False

import requests
import json
import markdown
import re

class NoteUploader:
    def __init__(self, session_cookie=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        })
        
        if session_cookie:
            self.session.cookies.set("session", session_cookie, domain=".note.com")

    def get_headers(self):
        """
        Returns standard headers for Note.com API requests.
        """
        return {
            'Origin': 'https://note.com',
            'Referer': 'https://note.com/notes',
            'X-Requested-With': 'XMLHttpRequest',
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
            response = self.session.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            # Debug: Print all cookies
            print(f"[DEBUG] Cookies after login: {self.session.cookies.get_dict()}")

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

    def create_article(self, title, body_markdown, status='draft'):
        """
        Creates a new article on Note.com.
        """
        print(f"[INFO] Creating article: {title} (Status: {status})")
        
        body_html = self.markdown_to_html(body_markdown)
        print(f"[DEBUG] HTML Body Preview: {body_html[:500]}...")
        
        url = 'https://note.com/api/v1/text_notes'
        
        # Try sending full body in initial POST with headers
        payload = {
            'name': title,
            'body': body_html,
            'template_key': None
        }
        
        try:
            # Use session to preserve cookies
            response = self.session.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Debug: Print full response data to see if body was accepted
            print(f"[DEBUG] Create Response Data: {str(data)[:500]}...")
            
            note_id = data['data']['id']
            note_key = data['data']['key']
            print(f"[INFO] Draft created. ID: {note_id}, Key: {note_key}")

            if status == 'published':
                if self.publish_article(note_id, title, body_html):
                    print(f"[SUCCESS] Article published! Key: {note_key}")
                else:
                    print(f"[WARN] Failed to publish. Article remains as draft.")
            
            return f"https://note.com/notes/{note_key}"

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return None

    def publish_article(self, note_id, title, body):
        """
        Publishes a draft article.
        """
        print(f"[INFO] Publishing article (ID: {note_id})...")
        url = f'https://note.com/api/v1/text_notes/{note_id}'
        
        # For publishing, we try to update status. 
        # If body is already saved, maybe we don't need to send it again?
        # But let's send it just in case, matching the reference.
        payload = {
            'body': body,
            'name': title,
            'status': 'published'
        }
        
        try:
            response = self.session.put(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            print("[DEBUG] Publish (PUT) successful.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Publish (PUT) failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return False

    def markdown_to_html(self, markdown_text):
        """
        Simple Regex-based Markdown to HTML converter (from reference).
        """
        html = markdown_text
        
        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Lists
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # Bold/Italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Code blocks
        html = re.sub(r'```(.+?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        
        # Paragraphs
        paragraphs = html.split('\n\n')
        html = '\n'.join([f'<p>{p}</p>' if not p.strip().startswith('<') else p for p in paragraphs])
        
        return html
    pass

if __name__ == "__main__":
    # Mock test
    pass
