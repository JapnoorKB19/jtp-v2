import socket
from src.jtp_socket import JTPSocket

def run_server():
    print("Select Backend Protocol to listen on:")
    print("1. TCP")
    print("2. UDP")
    print("3. JTP (Custom Proposed Protocol)")
    choice = input("Choice (1/2/3): ").strip()
    
    host = '127.0.0.1'
    port = 9000
    
    html_content = "<html><body><h1>Welcome to the Server!</h1><p>Transported securely.</p></body></html>"
    http_response = (f"HTTP/1.1 200 OK\r\nContent-Length: {len(html_content)}\r\nConnection: close\r\n\r\n{html_content}").encode()

    if choice == '1':
        print(f"[*] Web Server listening on TCP {host}:{port}")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen(1)
        while True:
            conn, addr = server.accept()
            req = conn.recv(1024)
            print(f"[Web Server] Received TCP request from {addr}")
            conn.sendall(http_response)
            conn.close()
            
    elif choice == '2':
        print(f"[*] Web Server listening on UDP {host}:{port}")
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind((host, port))
        while True:
            req, addr = server.recvfrom(1024)
            print(f"[Web Server] Received UDP request from {addr}")
            server.sendto(http_response, addr)
            
    elif choice == '3':
        print(f"[*] Web Server listening on JTP {host}:{port}")
        server = JTPSocket(host=host, port=port, is_server=True)
        while True:
            req, addr = server.receive_reliable()
            print(f"[Web Server] Received JTP request from {addr}")
            server.send_reliable(http_response, addr)

if __name__ == "__main__":
    run_server()
