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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': '*/*',
            'Origin': 'https://editor.note.com',
            'Referer': 'https://editor.note.com/',
        }
        
        # Add XSRF-TOKEN if available
        xsrf_token = self.session.cookies.get("XSRF-TOKEN")
        if xsrf_token:
            headers['X-XSRF-TOKEN'] = xsrf_token
            
        return headers

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

    def create_article(self, title, body_markdown, status='draft'):
        """
        Creates a new article on Note.com using the correct 2-step process.
        """
        print(f"[INFO] Creating article: {title} (Status: {status})")
        
        body_html = self.markdown_to_html(body_markdown)
        
        # Step 1: Create Draft (Minimal Payload)
        url_create = 'https://note.com/api/v1/text_notes'
        payload_create = {"template_key": None}
        
        try:
            response = self.session.post(url_create, headers=self.get_headers(), json=payload_create)
            response.raise_for_status()
            data = response.json()
            
            note_id = data['data']['id']
            note_key = data['data']['key']
            print(f"[INFO] Draft created. ID: {note_id}, Key: {note_key}")
            
            # Step 2: Update Content & Publish (PUT)
            # We combine update and publish into one PUT request if status is published
            final_status = 'published' if status == 'published' else 'draft'
            
            if self.update_article(note_id, note_key, title, body_html, status=final_status):
                if final_status == 'published':
                    print(f"[SUCCESS] Article published! Key: {note_key}")
                else:
                    print(f"[SUCCESS] Draft saved. Key: {note_key}")
            else:
                print(f"[ERROR] Failed to save/publish content.")
                return None
            
            return f"https://note.com/notes/{note_key}"

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Creation process failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return None

    def update_article(self, note_id, note_key, title, body, status='draft'):
        """
        Updates an existing article with full payload.
        """
        print(f"[INFO] Updating article (ID: {note_id})...")
        url = f'https://note.com/api/v1/text_notes/{note_id}'
        
        # Full payload based on GitHub30/note-mcp-server
        payload = {
            "author_ids": [],
            "body_length": len(body),
            "disable_comment": False,
            "exclude_from_creator_top": False,
            "exclude_ai_learning_reward": False,
            "free_body": body, # Correct field for body!
            "hashtags": [], # We could pass hashtags here if we had them
            "image_keys": [],
            "index": False,
            "is_refund": False,
            "limited": False,
            "magazine_ids": [],
            "magazine_keys": [],
            "name": title,
            "pay_body": "",
            "price": 0,
            "send_notifications_flag": True,
            "separator": None,
            "slug": f"slug-{note_key}",
            "status": status,
            "circle_permissions": [],
            "discount_campaigns": [],
            "lead_form": {"is_active": False, "consent_url": ""},
            "line_add_friend": {"is_active": False, "keyword": "", "add_friend_url": ""},
            "line_add_friend_access_token": "",
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
        # Deprecated, logic moved to create_article/update_article
        pass

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
