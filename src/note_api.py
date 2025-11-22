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
        Creates a new article on Note.com using a 3-step process:
        1. Create Draft (POST)
        2. Update Content (PUT)
        3. Publish (PUT) - if requested
        """
        print(f"[INFO] Starting article creation process: {title}")
        
        body_html = self.markdown_to_html(body_markdown)
        print(f"[DEBUG] HTML Body Preview: {body_html[:500]}...")
        
        # Step 1: Create Draft (Minimal Payload)
        url_create = 'https://note.com/api/v1/text_notes'
        payload_create = {
            'name': title,
            'body': '', # Try empty body first to just get ID
            'template_key': None
        }
        
        try:
            response = self.session.post(url_create, headers=self.get_headers(), json=payload_create)
            response.raise_for_status()
            data = response.json()
            
            note_id = data['data']['id']
            note_key = data['data']['key']
            print(f"[INFO] Step 1: Draft created. ID: {note_id}, Key: {note_key}")
            
            # Step 2: Update Content (Save Draft)
            if self.update_article(note_id, title, body_html, status='draft'):
                print(f"[INFO] Step 2: Content saved successfully.")
            else:
                print(f"[ERROR] Step 2: Failed to save content.")
                return None

            # Step 3: Publish (if requested)
            if status == 'published':
                if self.publish_article(note_id, title, body_html):
                    print(f"[SUCCESS] Step 3: Article published! Key: {note_key}")
                else:
                    print(f"[WARN] Step 3: Failed to publish. Article remains as draft.")
            
            return f"https://note.com/notes/{note_key}"

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Creation process failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return None

    def update_article(self, note_id, title, body, status='draft'):
        """
        Updates an existing article (draft).
        """
        print(f"[INFO] Updating article (ID: {note_id})...")
        url = f'https://note.com/api/v1/text_notes/{note_id}'
        
        payload = {
            'body': body,
            'name': title,
            'status': status,
            'template_key': None,
            'eyecatch_image_key': None
        }
        
        try:
            response = self.session.put(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            print("[DEBUG] Update (PUT) successful.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Update (PUT) failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return False

    def publish_article(self, note_id, title, body):
        """
        Publishes a draft article.
        """
        return self.update_article(note_id, title, body, status='published')

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
