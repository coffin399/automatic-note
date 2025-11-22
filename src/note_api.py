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

    def markdown_to_html(self, markdown_text):
        """
        Converts Markdown to HTML suitable for Note.com.
        """
        return markdown.markdown(markdown_text)

    def create_article(self, title, body_markdown, status="draft"):
        """
        Creates a new article on Note.com.
        status: 'draft' or 'published' (default: 'draft')
        """
        print(f"[INFO] Uploading article: {title} (Status: {status})")
        
        body_html = self.markdown_to_html(body_markdown)
        print(f"[DEBUG] HTML Body Preview: {body_html[:500]}...")
        
        url = 'https://note.com/api/v1/text_notes'
        
        # Try multiple fields to ensure body is captured
        payload = {
            'name': title,
            'body': body_html,
            'content': body_html,  # Potential alternative
            'text': body_html,     # Potential alternative
            'template_key': None
        }
        
        try:
            # Use session to preserve cookies
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
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
        Publishes a draft article by updating it with status='published'.
        """
        print(f"[INFO] Publishing article (ID: {note_id})...")
        
        # Use PUT to text_notes/{id} as per reference
        url = f'https://note.com/api/v1/text_notes/{note_id}'
        
        payload = {
            'name': title,
            'body': body,
            'status': 'published',
            'share_to_twitter': False,
            'share_to_facebook': False
        }
        
        try:
            response = self.session.put(url, json=payload)
            response.raise_for_status()
            print("[DEBUG] Publish (PUT) successful.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[WARN] Publish (PUT) failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return False

if __name__ == "__main__":
    # Mock test
    pass
