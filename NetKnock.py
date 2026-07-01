import socket
import threading
import sys
import time
from datetime import datetime

# --- GLOBALS ---
open_ports = []
lock = threading.Lock()

# --- FUNCTIONS ---

def grab_banner(ip, port):
    """Try to grab a banner from an open port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((ip, port))
        sock.send(b"HEAD / HTTP/1.1\r\n\r\n")
        banner = sock.recv(1024).decode().strip()
        sock.close()
        return banner[:60]  # Trim long banners
    except:
        return "No banner"

def scan_port(ip, port, timeout=2):
    """Scan a single port and grab banner if open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        if result == 0:
            banner = grab_banner(ip, port)
            with lock:
                open_ports.append((port, banner))
                print(f"[+] Port {port} OPEN → {banner}")
        sock.close()
    except:
        pass

def scan_ports(ip, start_port, end_port, threads=100, timeout=2):
    """Scan a range of ports using threading."""
    print(f"\n[+] Scanning {ip} from port {start_port} to {end_port} with {threads} threads...\n")
    start_time = time.time()

    thread_list = []
    for port in range(start_port, end_port + 1):
        t = threading.Thread(target=scan_port, args=(ip, port, timeout))
        thread_list.append(t)
        t.start()

        if len(thread_list) >= threads:
            for t in thread_list:
                t.join()
            thread_list = []

    # Wait for remaining threads
    for t in thread_list:
        t.join()

    elapsed = time.time() - start_time
    print(f"\n[+] Scan completed in {elapsed:.2f} seconds.")
    print(f"[+] {len(open_ports)} open ports found.")

def save_results(ip, open_ports):
    """Save scan results to a timestamped file."""
    if not open_ports:
        print("[!] No open ports to save.")
        return

    filename = f"scan_{ip.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w") as f:
        f.write(f"Scan results for {ip}\n")
        f.write(f"Open ports: {len(open_ports)}\n\n")
        for port, banner in open_ports:
            f.write(f"Port {port}: {banner}\n")
    print(f"[+] Results saved to {filename}")

# --- MAIN ---

if __name__ == "__main__":
    print("=== PORT SCANNER ===\n")

    # --- USER INPUT WITH DEFAULTS ---
    target = input("Enter IP or domain: ")
    try:
        ip = socket.gethostbyname(target)
        print(f"[+] Resolved {target} → {ip}\n")
    except:
        print("[-] Invalid domain or IP.")
        sys.exit(1)

    start_input = input("Start port (default 1): ")
    start_port = int(start_input) if start_input.strip() else 1

    end_input = input("End port (default 1024): ")
    end_port = int(end_input) if end_input.strip() else 1024

    threads_input = input("Number of threads (default 100): ")
    threads = int(threads_input) if threads_input.strip() else 100

    # --- RUN SCAN ---
    scan_ports(ip, start_port, end_port, threads)

    # --- SAVE RESULTS ---
    save_results(ip, open_ports)

    print("\n[+] Done.")