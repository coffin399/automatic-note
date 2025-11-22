import sys
import os
import random
import time
from datetime import datetime
from config import load_config, validate_config
from scraper import WebScraper
from generator import GeminiGenerator
from note_api import NoteUploader

def run_report(config, scraper, generator, uploader):
    """
    Executes a single reporting cycle.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting report generation cycle...")

    # 3. Determine Topics (Genres)
    genres = config.get('topic_genres', ["金融", "政治", "カルチャー", "サブカルチャー"])
    print(f"[INFO] Target Genres: {genres}")

    # 4. Scrape Info for EACH Genre
    print("[INFO] Scraping information...")
    all_search_results = {}
    
    for genre in genres:
        print(f"  - Scraping for: {genre}")
        # Search for "Genre + News + Date/Recent"
        results = scraper.search([genre, "ニュース", "最新"], max_results=3)
        if results:
            all_search_results[genre] = results
        else:
            print(f"    [WARN] No results for {genre}")
            all_search_results[genre] = []
        
        # Be polite to search engines
        time.sleep(1) 

    if not any(all_search_results.values()):
        print("[ERROR] No search results found for any genre. Skipping this cycle.")
        return

    # 5. Generate Content (Aggregated)
    print("[INFO] Generating report...")
    # Title format: YYYY-MM-DD 簡単レポート
    today_str = datetime.now().strftime("%Y-%m-%d")
    title = f"{today_str} 簡単レポート"
    
    article_body = generator.generate_article(title, all_search_results)
    if not article_body:
        print("[ERROR] Content generation failed. Skipping this cycle.")
        return

    print(f"\n--- Generated Report ---\nTitle: {title}\nLength: {len(article_body)} chars\n------------------------\n")

    # 6. Upload to Note
    upload_status = config.get('upload_status', 'draft')
    print(f"[INFO] Uploading to Note.com as {upload_status}...")
    
    note_url = uploader.create_article(title, article_body, status=upload_status)
    
    if note_url:
        print(f"\n[SUCCESS] Article created successfully!\nURL: {note_url}")
    else:
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
    scraper = WebScraper()
    generator = GeminiGenerator(
        api_key=config['gemini_api_key'],
        system_prompt=config['system_prompt']
    )
    uploader = NoteUploader(session_cookie=config['note_session_cookie'])

    # --- Execution Loop ---
    
    # 1. Run Immediately on Startup
    print("\n[SCHEDULE] Running startup job...")
    run_report(config, scraper, generator, uploader)

    # 2. Enter Scheduler Loop
    print("\n[SCHEDULE] Waiting for next scheduled time (08:00 or 20:00)...")
    print("Press Ctrl+C to stop.")
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        if current_time in ["08:00", "20:00"]:
            print(f"\n[SCHEDULE] It's {current_time}! Starting scheduled job.")
            run_report(config, scraper, generator, uploader)
            # Wait 61 seconds to ensure we don't run again in the same minute
            time.sleep(61)
        
        # Check every 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    main()
