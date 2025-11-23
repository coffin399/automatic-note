import sys
import os
import random
import time
from datetime import datetime
from config import load_config, validate_config
from generator import GeminiGenerator
from note_api import NoteUploader

def run_report(config, generator, uploader):
    """
    Executes a single reporting cycle.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting report generation cycle...")

    # 3. Determine Topics (Genres)
    genres = config.get('topic_genres', ["金融", "政治", "カルチャー", "サブカルチャー"])
    print(f"[INFO] Target Genres: {genres}")

    # 4. Generate Content (Gemini Grounding)
    print("[INFO] Generating report with Gemini Grounding...")
    # Title format: YYYY-MM-DD 午前/午後レポート
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_hour = datetime.now().hour
    period = "午前" if current_hour < 12 else "午後"
    title = f"{today_str} {period}レポート"
    
    article_body = generator.generate_article(genres)
    if not article_body:
        print("[ERROR] Content generation failed. Skipping this cycle.")
        print("\n[ERROR] Failed to create article.")

def main():
    print("=== Note.com AI Writer (Scheduled Mode) ===")
    print("Schedule: Startup, 08:00, 20:00")
    
    # 1. Load Config
    try:
        config = load_config()
    except Exception as e:
        print(f"[FATAL] {e}")
        sys.exit(1)

    if not validate_config(config):
        print("[INFO] Please update config.yaml and run again.")
        sys.exit(0)

    # 2. Initialize Components
    generator = GeminiGenerator(
        api_key=config['gemini_api_key'],
        model_name=config.get('gemini_model', 'gemini-2.0-flash-exp'),
        system_prompt=config['system_prompt']
    )
    
    # Handle Note Auth
    session_cookie = config.get('note_session_cookie')
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
                print("[FATAL] Auto-login failed. Please check credentials or use session cookie.")
                sys.exit(1)
        else:
            print("[FATAL] No session cookie and no credentials provided.")
            sys.exit(1)

    # --- Execution Loop ---
    
    # 1. Run Immediately on Startup
    print("\n[SCHEDULE] Running startup job...")
    run_report(config, generator, uploader)

    # 2. Enter Scheduler Loop
    print("\n[SCHEDULE] Waiting for next scheduled time (08:00 or 20:00)...")
    print("Press Ctrl+C to stop.")
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        if current_time in ["08:00", "20:00"]:
            print(f"\n[SCHEDULE] It's {current_time}! Starting scheduled job.")
            run_report(config, generator, uploader)
            # Wait 61 seconds to ensure we don't run again in the same minute
            time.sleep(61)
        
        # Check every 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    main()
