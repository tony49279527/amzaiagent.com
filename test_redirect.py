import urllib.request
import urllib.error
import threading
import sys
import os

# Set environment variable to run server on a different port for testing
os.environ['PORT'] = '8081'

def run_server():
    import server

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

import time
time.sleep(2)

try:
    url = 'http://localhost:8081/blog-post.html?id=amazon-gmv-growth-2025-record-milestone'
    req = urllib.request.Request(url, method='HEAD')
    
    # We want to catch the redirect and not let urllib handle it automatically
    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def http_error_301(self, req, fp, code, msg, headers):
            return urllib.response.addinfourl(fp, headers, req.get_full_url(), code)
            
    opener = urllib.request.build_opener(NoRedirectHandler)
    response = opener.open(req)
    
    print(f"Status Code: {response.status}")
    print(f"Location Header: {response.headers.get('Location')}")
    
    if response.status == 301 and response.headers.get('Location') == '/blog/amazon-gmv-growth-2025-milestone.html':
        print("Redirect successfully verified.")
    else:
        print("Redirect verification failed.")
except Exception as e:
    print(f"Error testing server: {e}")
