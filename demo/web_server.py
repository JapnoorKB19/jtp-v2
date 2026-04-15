import socket
from src.jtp_socket import JTPServer

def run_server():
    print("Select Backend Protocol to listen on:")
    print("1. TCP")
    print("2. UDP")
    print("3. JTP V2 (Multi-threaded & Windowed)")
    choice = input("Choice (1/2/3): ").strip()
    
    host = '127.0.0.1'
    port = 9000
    
    if choice == '1':
        print(f"[*] Web Server listening on TCP {host}:{port}")
        # Standard TCP code remains unchanged...
            
    elif choice == '2':
        print(f"[*] Web Server listening on UDP {host}:{port}")
        # Standard UDP code remains unchanged...
            
    elif choice == '3':
        # V2 Engine handles the dispatching automatically
        server = JTPServer(host=host, port=port)
        server.start()

if __name__ == "__main__":
    run_server()
