import socket
import threading
from src.jtp_socket import JTPSocket

class LocalProxy:
    def __init__(self, protocol_choice, tcp_port=8080, target_ip='127.0.0.1', target_port=9000):
        self.tcp_port = tcp_port
        self.target = (target_ip, target_port)
        self.protocol = protocol_choice
        
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server.bind(('127.0.0.1', self.tcp_port))
        self.tcp_server.listen(5)

    def handle_client(self, tcp_client):
        request_data = tcp_client.recv(4096)
        if not request_data: return
        
        print(f"\n[Proxy] Intercepted curl request. Tunneling via {self.protocol}...")
        
        try:
            # Route traffic based on user choice
            if self.protocol == 'TCP':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(self.target)
                sock.sendall(request_data)
                response_data = sock.recv(4096)
                sock.close()
                
            elif self.protocol == 'UDP':
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2.0)
                sock.sendto(request_data, self.target)
                response_data, _ = sock.recvfrom(4096)
                sock.close()
                
            elif self.protocol == 'JTP':
                jtp_client = JTPSocket()
                jtp_client.send_reliable(request_data, self.target)
                response_data, _ = jtp_client.receive_reliable()
            
            # Return response to curl
            tcp_client.sendall(response_data)
            print(f"[Proxy] Response received. Returning to curl.")
            
        except Exception as e:
            print(f"[!] Tunneling error: {e}")
        finally:
            tcp_client.close()

    def start(self):
        print(f"[*] Proxy listening for curl on http://127.0.0.1:{self.tcp_port}")
        print(f"[*] Tunneling traffic to backend using: {self.protocol}")
        while True:
            client_sock, addr = self.tcp_server.accept()
            threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
