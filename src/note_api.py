import requests
import json
import re
import os
import markdown

class NoteUploader:
    def __init__(self, session_cookie=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        })
        
        if session_cookie:
            self.session.cookies.set("session", session_cookie, domain=".note.com")
            # Also set for note.com just in case
            self.session.cookies.set("session", session_cookie, domain="note.com")

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

    def upload_image(self, file_path):
        """
        Uploads an image to Note.com and returns the image key.
        """
        if not os.path.exists(file_path):
            print(f"[ERROR] Image file not found: {file_path}")
            return None

        print(f"[INFO] Uploading image: {file_path}")
        # Endpoint from article: https://note.com/taku_sid/n/n1b1b7894e28f
        url = 'https://note.com/api/v1/upload_image'
        
        try:
            with open(file_path, 'rb') as f:
                # The article suggests 'file' as the key
                files = {'file': (os.path.basename(file_path), f, 'image/png')}
                
                # Note: The article didn't use 'data', so we try without it first.
                # If we need 'type', we can add it back.
                
                response = self.session.post(url, headers=self.get_headers(), files=files)
                response.raise_for_status()
                
                data = response.json()
                if 'data' in data and 'key' in data['data']:
                    image_key = data['data']['key']
                    print(f"[SUCCESS] Image uploaded. Key: {image_key}")
                    return image_key
                else:
                    print(f"[ERROR] Unexpected upload response: {data}")
                    return None
                    
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Image upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ERROR] Response: {e.response.text}")
            return None

    def create_article(self, title, body_markdown, status='draft', eyecatch_path=None):
        """
        Creates a new article on Note.com using the correct 2-step process.
        """
        print(f"[INFO] Creating article: {title} (Status: {status})")
        
        # Extract hashtags and convert body
        hashtags, body_html = self.process_markdown(body_markdown)
        
        # Upload Eyecatch if provided
        eyecatch_key = None
        if eyecatch_path:
            eyecatch_key = self.upload_image(eyecatch_path)

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
            
            if self.update_article(note_id, note_key, title, body_html, hashtags, status=final_status, eyecatch_key=eyecatch_key):
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

    def update_article(self, note_id, note_key, title, body, hashtags, status='draft', eyecatch_key=None):
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
            "free_body": body,
            "hashtags": hashtags, 
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
        
        if eyecatch_key:
            payload["eyecatch_image_key"] = eyecatch_key
            payload["image_keys"].append(eyecatch_key)
        
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

    def process_markdown(self, markdown_text):
        """
        Extracts hashtags and converts Markdown to HTML using markdown library.
        """
        # 1. Extract Hashtags (for metadata, if it works)
        hashtags = re.findall(r'#(\S+)', markdown_text)
        
        # 2. Convert to HTML using markdown library
        # We NO LONGER strip hashtags from the body. They will appear as plain text.
        html = markdown.markdown(markdown_text)
        
        return hashtags, html

    def markdown_to_html(self, markdown_text):
        # Deprecated, use process_markdown
        _, html = self.process_markdown(markdown_text)
        return html
