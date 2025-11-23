import os
import requests
import sys

MODEL_URL = "https://civitai.com/api/download/models/119632" # Shiitake Mix v1.0 (Approx ID based on search, verifying...)
# Wait, the user gave ID 1066229. Let's use that if it's the version ID.
# Civitai URL: https://civitai.com/models/1066229/shiitake-mix
# Usually the ID in the URL is the Model ID, not Version ID.
# But if it's a specific version page, it might be Version ID.
# Let's try to fetch the model metadata first to get the correct download link.

def get_download_url(model_id):
    # Try to get model info
    api_url = f"https://civitai.com/api/v1/models/{model_id}"
    print(f"Fetching metadata from {api_url}...")
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            # Get the first version's download URL
            if 'modelVersions' in data and len(data['modelVersions']) > 0:
                version = data['modelVersions'][0]
                download_url = version['downloadUrl']
                filename = version['files'][0]['name']
                print(f"Found model: {data['name']} - Version: {version['name']}")
                return download_url, filename
    except Exception as e:
        print(f"Error fetching metadata: {e}")
    
    # Fallback: Try direct download if ID is version ID
    return f"https://civitai.com/api/download/models/{model_id}", "ShiitakeMix.safetensors"

def download_file(url, filename):
    os.makedirs("models", exist_ok=True)
    filepath = os.path.join("models", filename)
    
    if os.path.exists(filepath):
        print(f"File {filepath} already exists. Skipping download.")
        return

    print(f"Downloading {filename} from {url}...")
    print("This may take a while (approx 2GB+)...")
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_length = int(r.headers.get('content-length', 0))
            dl = 0
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    if chunk: 
                        dl += len(chunk)
                        f.write(chunk)
                        done = int(50 * dl / total_length) if total_length else 0
                        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f} MB")
                        sys.stdout.flush()
        print("\nDownload complete!")
    except Exception as e:
        print(f"\nDownload failed: {e}")

if __name__ == "__main__":
    # User provided ID: 1066229
    # Note: Civitai IDs in URLs like /models/12345 are usually Model IDs.
    # The API /api/v1/models/12345 returns model info including versions.
    model_id = "1066229" 
    
    # However, sometimes the ID in the URL IS the version ID if it's a specific link.
    # Let's try to fetch metadata for 1066229.
    # If it fails, we assume it's a version ID and try direct download.
    
    url, filename = get_download_url(model_id)
    download_file(url, filename)
