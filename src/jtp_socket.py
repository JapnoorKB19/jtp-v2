import socket
import threading
import time
from src.jtp_header import JTPHeader, FLAG_DATA, FLAG_ACK, FLAG_FIN

CHUNK_SIZE = 1400
WINDOW_SIZE = 5     # Send 5 packets before waiting for ACKs (Go-Back-N style)
TIMEOUT = 0.5

class JTPSocket:
    """Handles an individual, reliable JTP connection with Windowing and Teardown."""
    def __init__(self, target_addr=None, existing_sock=None):
        self.target_addr = target_addr
        self.sock = existing_sock or socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if not existing_sock:
            self.sock.settimeout(TIMEOUT)
            
        self.seq_num = 1000
        self.expected_ack = 1000
        self.state = "ESTABLISHED"
        
        # Buffer for incoming data
        self.receive_buffer = b""

    def send_reliable(self, data, addr=None):
        """Window-based sender (Allows multiple in-flight packets)."""
        target = addr or self.target_addr
        chunks = [data[i:i+CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
        total_chunks = len(chunks)
        
        base = 0
        while base < total_chunks:
            window_end = min(base + WINDOW_SIZE, total_chunks)
            for i in range(base, window_end):
                chunk = chunks[i]
                current_seq = self.seq_num + i
                header = JTPHeader(flags=FLAG_DATA, seq_num=current_seq, payload_len=len(chunk), payload=chunk)
                packet = header.pack() + chunk
                self.sock.sendto(packet, target)
            
            ack_received = False
            start_time = time.time()
            while time.time() - start_time < TIMEOUT:
                try:
                    resp, peer_addr = self.sock.recvfrom(2048)
                    resp_hdr = JTPHeader.unpack(resp)
                    if resp_hdr.flags == FLAG_ACK and resp_hdr.ack_num >= self.seq_num + window_end:
                        base = window_end
                        self.seq_num = resp_hdr.ack_num
                        ack_received = True
                        
                        # --- UDP SESSION MIGRATION FIX ---
                        # If the server thread replied from a new ephemeral port, lock onto it!
                        if self.target_addr and peer_addr != self.target_addr:
                            self.target_addr = peer_addr
                            target = peer_addr
                        # ---------------------------------
                        break
                except (socket.timeout, ValueError):
                    continue
            
            if not ack_received:
                print(f"[JTP] Timeout. Sliding Window retransmitting from sequence {self.seq_num + base}...")

    def receive_reliable(self):
        """Receives data and handles FIN teardown requests."""
        while self.state != "CLOSED":
            try:
                packet, peer_addr = self.sock.recvfrom(2048)
                header = JTPHeader.unpack(packet)
                
                # --- UDP SESSION MIGRATION FIX ---
                # Ensure the FIN handshake goes back to the exact thread that sent the data
                if not self.target_addr or self.target_addr != peer_addr:
                    self.target_addr = peer_addr
                # ---------------------------------

                if header.flags == FLAG_FIN:
                    print(f"[JTP] FIN received from {peer_addr}. Closing connection.")
                    self._send_ack(peer_addr, header.seq_num + 1)
                    self.state = "CLOSED"
                    return b"", peer_addr
                    
                if header.flags == FLAG_DATA:
                    self.receive_buffer += header.payload
                    self.expected_ack = header.seq_num + 1
                    self._send_ack(peer_addr, self.expected_ack)
                    
                    data = self.receive_buffer
                    self.receive_buffer = b""
                    return data, peer_addr
                    
            except socket.timeout:
                continue
            except ValueError:
                pass

    def _send_ack(self, addr, ack_num):
        ack_hdr = JTPHeader(flags=FLAG_ACK, ack_num=ack_num)
        self.sock.sendto(ack_hdr.pack(), addr)

    def close(self):
        """Formal FIN/ACK 4-way handshake teardown."""
        if self.state == "CLOSED": return
        self.state = "FIN_WAIT"
        print(f"[JTP] Initiating FIN/ACK teardown to {self.target_addr}...")
        
        fin_hdr = JTPHeader(flags=FLAG_FIN, seq_num=self.seq_num)
        self.sock.sendto(fin_hdr.pack(), self.target_addr)
        
        # Wait for FIN-ACK
        try:
            resp, _ = self.sock.recvfrom(2048)
            resp_hdr = JTPHeader.unpack(resp)
            if resp_hdr.flags == FLAG_ACK:
                print("[JTP] Teardown complete. Socket closed gracefully.")
                self.state = "CLOSED"
        except socket.timeout:
            pass
        self.sock.close()


class JTPServer:
    """Multi-threaded Dispatcher: Routes raw UDP packets to isolated client handlers."""
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.main_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.main_sock.bind((self.host, self.port))
        self.clients = {}  # Maps addresses to JTPSocket connection objects
        print(f"[*] JTP Multi-Threaded Server listening on {host}:{port}")

    def handle_client(self, data, addr, initial_packet):
        """Runs in a dedicated thread for a specific client."""
        # Create a dedicated socket for this specific client session
        client_conn = JTPSocket(target_addr=addr)
        
        try:
            header = JTPHeader.unpack(initial_packet)
            if header.flags == FLAG_DATA:
                client_conn._send_ack(addr, header.seq_num + 1)
                
                # Example Application layer response (Web Server)
                html = "<html><body><h1>JTP V2 Enterprise Server</h1><p>Multithreaded & Windowed</p></body></html>"
                resp = (f"HTTP/1.1 200 OK\r\nContent-Length: {len(html)}\r\nConnection: close\r\n\r\n{html}").encode()
                
                client_conn.send_reliable(resp, addr)
                client_conn.close()  # Trigger the new FIN/ACK teardown
                
        except ValueError:
            pass # Drop corrupted
        finally:
            if addr in self.clients:
                del self.clients[addr]

    def start(self):
        """Dispatcher Loop."""
        while True:
            packet, addr = self.main_sock.recvfrom(2048)
            if addr not in self.clients:
                print(f"[Dispatcher] New concurrent client detected: {addr}. Spinning up thread.")
                # Create a placeholder to prevent duplicate threads
                self.clients[addr] = True 
                # Dispatch worker thread
                thread = threading.Thread(target=self.handle_client, args=(None, addr, packet))
                thread.start()
