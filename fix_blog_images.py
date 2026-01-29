
import requests
import urllib.parse
import time
import os
import random

def generate_and_save(original_title, filename):
    print(f"Fixing image for: {original_title}")
    
    # 1. FIXED STYLE PROMPT
    style_prompt = "isometric 3d illustration, soft studio lighting, amazon aws brand colors (dark blue and orange), clean minimalist background, high quality 3d render, unreal engine 5, 4k"
    
    # 2. CONTENT PROMPT
    subject = original_title.lower()
    subject = subject.replace("amazon", "").replace("fba", "").replace("2026", "").replace("update", "")
    import re
    subject = re.sub(r'[^\w\s]', '', subject).strip()
    
    final_prompt = f"{subject}, {style_prompt}"
    
    encoded_prompt = urllib.parse.quote(final_prompt)
    
    # Use a large random seed range to ensure legitimate new request
    seed = random.randint(10000, 99999)
    # Add width/height to matches common blog formats
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=800&height=450&nologo=true"
    
    print(f"Target URL: {image_url}")
    
    image_path = f"assets/images/blog_thumbs/{filename}"
    
    try:
        resp = requests.get(image_url, timeout=90) # Increased timeout
        
        if resp.status_code == 200:
            # Basic validation: check if it's the error image by size?
            # The error image seems to be around ~1.3MB or exactly uniform. 
            # Real images vary. 
            
            with open(image_path, 'wb') as f:
                f.write(resp.content)
            print(f"SUCCESS: Saved to {image_path} (Size: {len(resp.content)} bytes)")
            return True
        else:
            print(f"FAILED: Status {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    # The list of files that we identified as duplicates/errors
    targets = [
        {
            "title": "Amazon SAFE-T Claims Window Reduced to 30 Days: Critical 2026 Update for FBA Sellers",
            "file": "amazon-safe-t-claims-window-changes-2026.png" 
        },
        {
             "title": "Amazon SAFE-T Claims Window Reduction 2026: What Sellers Must Know",
             "file": "amazon-safe-t-claims-window-reduction-2026.png"
        },
        {
             "title": "Amazon SAFE-T Claims Window Change 2026: 30-Day Limit Impact on Sellers",
             "file": "amazon-safe-t-claims-window-change-2026.png"
        }
    ]
    
    for target in targets:
        success = False
        attempts = 0
        while not success and attempts < 3:
            attempts += 1
            success = generate_and_save(target['title'], target['file'])
            if not success:
                print(f"Retry {attempts}...")
                time.sleep(5)
        
        # Long sleep between different files to avoid hitting rate limit again
        print("Sleeping 15 seconds to avoid rate limits...")
        time.sleep(15)

if __name__ == "__main__":
    main()
