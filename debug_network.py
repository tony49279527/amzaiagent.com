import socket
import sys

def check_port(host, port):
    print(f"Testing connectivity to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5) # 5 second timeout
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f" [SUCCESS] Port {port} is OPEN and reachable.")
            # Try to grab banner if possible (only for non-SSL ports usually, but good check)
            try:
                banner = sock.recv(1024)
                print(f" Banner: {banner.decode('utf-8', errors='ignore').strip()}")
            except:
                pass
        else:
            print(f" [FAIL] Port {port} is CLOSED or BLOCKED (Error Code: {result}).")
        sock.close()
    except Exception as e:
        print(f" [ERROR] Connection failed: {e}")

if __name__ == "__main__":
    host = "142.251.10.108" # Known Google SMTP IP
    ports = [465, 587, 25]
    
    print(f"--- Network Connectivity Check for {host} ---")
    for port in ports:
        check_port(host, port)
