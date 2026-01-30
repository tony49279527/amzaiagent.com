
from PIL import Image
import os

png_path = "assets/images/blog_thumbs/amazon-safe-t-claims-window-30-days-2026-update.png"
webp_path = "assets/images/blog_thumbs/amazon-safe-t-claims-window-30-days-2026-update.webp"

if os.path.exists(png_path):
    img = Image.open(png_path)
    img.save(webp_path, "WEBP")
    print(f"Converted {png_path} to {webp_path}")
else:
    print(f"File not found: {png_path}")
