
import json
import re
import os
import urllib.parse
import requests
import time

def clean_title_for_prompt(title):
    # Simplify title for better image generation
    # Remove special chars and keep key concepts
    clean = re.sub(r'[^\w\s]', '', title)
    return clean

def generate_image(title, slug):
    print(f"Generating image for: {title}")
    
    # 1. FIXED STYLE PROMPT (The "System" Prompt)
    # Defines the consistent look and feel
    style_prompt = "isometric 3d illustration, soft studio lighting, amazon aws brand colors (dark blue and orange), clean minimalist background, high quality 3d render, unreal engine 5, 4k"
    
    # 2. CONTENT PROMPT (The "User" Prompt)
    # Extracts the core subject from the title
    # We want to remove "Amazon", "FBA", "2026" fluff to focus on the visual object
    subject = title.lower()
    subject = subject.replace("amazon", "").replace("fba", "").replace("2026", "").replace("update", "")
    subject = re.sub(r'[^\w\s]', '', subject).strip()
    
    # Combine them: "[Subject], [Style]"
    final_prompt = f"{subject}, {style_prompt}"
    
    encoded_prompt = urllib.parse.quote(final_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    
    image_filename = f"{slug}.png"
    # Ensure directory exists
    os.makedirs("assets/images/blog_thumbs", exist_ok=True)
    image_path = f"assets/images/blog_thumbs/{image_filename}"
    
    try:
        # Pass a random seed to ensure uniqueness per call
        import random
        image_url += f"?seed={random.randint(0, 10000)}&width=800&height=450&nologo=true"
        
        print(f"Downloading from: {image_url}")
        resp = requests.get(image_url, timeout=60)
        
        if resp.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(resp.content)
            print(f"Saved to: {image_path}")
            return image_path
        else:
            print(f"Failed to download. Status: {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

def main():
    js_path = "data/blog/blog_posts.js"
    
    try:
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract the blogPostsEN array
        match = re.search(r'window\.blogPostsEN\s*=\s*(\[[\s\S]*?\]);', content)
        if not match:
            print("Could not find blogPostsEN array")
            return

        blog_posts = json.loads(match.group(1))
        
        # We only want to update the first 5 posts
        posts_to_update = blog_posts[:5]
        
        for post in posts_to_update:
            new_image_path = generate_image(post['title'], post['id'])
            if new_image_path:
                # Update the post object
                post['cover_image'] = new_image_path
                
                # Also try to update the image inside 'content' HTML if it contains a placeholder or old image
                # We simply check if there's an img tag early in content and try to replace it or inject one
                # For safety, let's just ensure the cover_image field is correct. 
                # The user asked to "replace the pictures of the last 5 blog posts", 
                # implying the cover/thumbnail.
                
                # However, looking at the data, there is also an <img> tag inside content.
                # Let's try to replace the first img src in content if possible
                if 'content' in post:
                    soup_match = re.search(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', post['content'])
                    if soup_match:
                        # Replace the src with new image path (need to adjust relative path if needed)
                        # The blog usually uses relative paths. 
                        # If the content currently points to external URL (like ecommercebytes), replace it.
                        old_src = soup_match.group(1)
                        # We use the same image for content as cover
                        post['content'] = post['content'].replace(old_src, new_image_path)
            
            # Be nice to the API and avoid rate limits
            time.sleep(10)

        # Now write back the updated array
        # Reconstruct the file content
        
        # We need to preserve the formatting reasonably well
        # The original file has `window.blogPostsCN = [];` then `window.blogPostsEN = [...]`
        
        # Let's just rewrite the whole file structure we know exists
        new_js_content = f"""
window.blogPostsCN = [];
window.blogPostsEN = {json.dumps(blog_posts, indent=2, ensure_ascii=False)};
"""
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(new_js_content)
            
        print("Successfully updated blog_posts.js with new images for top 5 posts.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
