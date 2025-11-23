import sys
import os
import random
import time
from datetime import datetime
from config import load_config, validate_config
from generator import GeminiGenerator
from note_api import NoteUploader
try:
    from image_generator import LocalImageGenerator
except ImportError:
    LocalImageGenerator = None

def run_report(config, generator, uploader, image_generator=None):
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
        return

    # Extract Title from Article Body (First Line)
    lines = article_body.strip().split('\n')
    if lines and len(lines) > 0:
        candidate_title = lines[0].strip()
        # Simple heuristic: If it's short and doesn't start with Markdown headers (unless it's the title header)
        # Remove common prefixes like "タイトル:" if present
        clean_title = candidate_title.replace("タイトル:", "").replace("Title:", "").strip()
        
        if len(clean_title) < 100: # Assuming titles aren't super long
            title = clean_title
            # Remove the title from the body to avoid duplication, 
            # but keep it if it was a markdown header so the body structure remains valid?
            # Actually, Note.com title is separate field. So we should remove it from body if it's just the title.
            # If the AI formatted it as "# Title", we remove that line.
            article_body = "\n".join(lines[1:]).strip()
            print(f"[INFO] Extracted AI Title: {title}")
        else:
             print(f"[INFO] First line too long for title, using default: {title}")

    print(f"\n--- Generated Report ---\nTitle: {title}\nLength: {len(article_body)} chars\nPreview: {article_body[:500]}...\n------------------------\n")

    # 6. Upload to Note.com
    upload_status = config.get('upload_status', 'draft')
    print(f"[INFO] Uploading to Note.com as {upload_status}...")
    
    # Determine eyecatch image
    eyecatch_path = None
    
    # Priority 0: Generate Image (if enabled)
    img_config = config.get('image_generation', {})
    if img_config.get('enabled', False) and image_generator:
        print("[INFO] Attempting to generate eyecatch image...")
        
        # Determine Prompt
        base_prompt = ""
        prompts_list = img_config.get('prompts', [])
        if prompts_list:
            base_prompt = random.choice(prompts_list)
            print(f"[INFO] Selected base prompt: {base_prompt}")
            
        context_prompt = ""
        if img_config.get('use_article_context', True):
            context_prompt = generator.generate_image_prompt(article_body)
            print(f"[INFO] Generated context prompt: {context_prompt}")
            
        # Combine prompts
        if base_prompt and context_prompt:
            image_prompt = f"{base_prompt}, {context_prompt}"
        elif base_prompt:
            image_prompt = base_prompt
        else:
            image_prompt = context_prompt
            
        print(f"[INFO] Final Image Prompt: {image_prompt}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"generated_{timestamp}.png"
        output_path = os.path.join("eyecatch", "generated", output_filename)
        
        generated_path = image_generator.generate(
            prompt=image_prompt,
            output_path=output_path,
            negative_prompt=img_config.get('negative_prompt'),
            width=img_config.get('width', 512),
            height=img_config.get('height', 512),
            num_inference_steps=img_config.get('steps', 20)
        )
        
        if generated_path:
            eyecatch_path = generated_path
            print(f"[SUCCESS] Generated image: {eyecatch_path}")
        else:
            print("[WARN] Image generation failed. Falling back to local files.")

    # Priority 1: Random image from 'eyecatch' folder (Fallback)
    if not eyecatch_path:
        eyecatch_dir = "eyecatch"
        if os.path.exists(eyecatch_dir) and os.path.isdir(eyecatch_dir):
            images = [
                os.path.join(eyecatch_dir, f) 
                for f in os.listdir(eyecatch_dir) 
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and "generated" not in f
            ]
            if images:
                eyecatch_path = random.choice(images)
                print(f"[INFO] Selected random eyecatch image: {eyecatch_path}")
    
    # Priority 2: Root eyecatch.png (Fallback)
    if not eyecatch_path and os.path.exists("eyecatch.png"):
        eyecatch_path = "eyecatch.png"
        print(f"[INFO] Using default eyecatch image: {eyecatch_path}")

    note_url = uploader.create_article(title, article_body, status=upload_status, eyecatch_path=eyecatch_path)
    
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
    generator = GeminiGenerator(
        api_key=config['gemini_api_key'],
        model_name=config.get('gemini_model', 'gemini-2.0-flash-exp'),
        system_prompt=config['system_prompt'],
        use_search=config.get('use_search', True)
    )
    
    # Initialize Image Generator if enabled
    image_generator = None
    img_config = config.get('image_generation', {})
    if img_config.get('enabled', False):
        if LocalImageGenerator:
            try:
                device = img_config.get('device', 'cpu')
                scheduler = img_config.get('scheduler', 'Euler a')
                print(f"[INIT] Initializing Local Image Generator config (Model: {img_config.get('model_id')}, Device: {device}, Scheduler: {scheduler})...")
                image_generator = LocalImageGenerator(
                    model_id=img_config.get('model_id', "runwayml/stable-diffusion-v1-5"),
                    device=device,
                    scheduler_name=scheduler
                )
            except Exception as e:
                print(f"[ERROR] Failed to initialize image generator: {e}")
        else:
            print("[WARN] LocalImageGenerator not found. Please install requirements.")

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
    run_report(config, generator, uploader, image_generator)

    # 2. Enter Scheduler Loop
    schedule_times = config.get('schedule_times', ["08:00", "20:00"])
    print(f"\n[SCHEDULE] Waiting for next scheduled time {schedule_times}...")
    print("Press Ctrl+C to stop.")
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        if current_time in schedule_times:
            print(f"\n[SCHEDULE] It's {current_time}! Starting scheduled job.")
            run_report(config, generator, uploader, image_generator)
            # Wait 61 seconds to ensure we don't run again in the same minute
            time.sleep(61)
        
        # Check every 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    main()
