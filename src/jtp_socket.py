import socket
import time
from src.jtp_header import JTPHeader

class JTPSocket:
    MAX_PAYLOAD_SIZE = 1400
    TIMEOUT = 1.0  # Seconds to wait for an ACK before retransmitting
    MAX_RETRIES = 5

    def __init__(self, host='127.0.0.1', port=None, is_server=False):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set a small timeout for non-blocking receive operations
        self.sock.settimeout(0.5) 
        self.seq_num = 1000  # Starting sequence number
        
        if is_server and port:
            self.sock.bind((host, port))
            print(f"[*] JTP Server listening on {host}:{port}")

    def send_reliable(self, data, dest_addr):
        """Chunks data, applies JTP headers, and ensures reliable delivery."""
        chunks = [data[i:i + self.MAX_PAYLOAD_SIZE] for i in range(0, len(data), self.MAX_PAYLOAD_SIZE)]
        
        for chunk in chunks:
            self._send_chunk_with_retry(chunk, dest_addr)
            self.seq_num += len(chunk) # Increment sequence number by bytes sent

    def _send_chunk_with_retry(self, chunk, dest_addr):
        """Handles the transmission and ACK waiting for a single chunk."""
        header = JTPHeader(
            flags=JTPHeader.FLAG_DATA,
            window_size=64,
            seq_num=self.seq_num,
            ack_num=0,
            payload_data=chunk
        )
        packet = header.pack() + chunk
        
        for attempt in range(self.MAX_RETRIES):
            self.sock.sendto(packet, dest_addr)
            # print(f"[->] Sent Seq: {self.seq_num}, Attempt: {attempt + 1}")
            
            if self._wait_for_ack(self.seq_num + len(chunk)):
                return  # ACK received, move to next chunk
                
            print(f"[!] Timeout! Retransmitting Seq: {self.seq_num}")
            
        raise ConnectionError(f"Failed to deliver packet {self.seq_num} after {self.MAX_RETRIES} retries.")

    def _wait_for_ack(self, expected_ack_num):
        """Listens for an ACK matching the expected sequence number."""
        start_time = time.time()
        while time.time() - start_time < self.TIMEOUT:
            try:
                raw_data, _ = self.sock.recvfrom(2048)
                if len(raw_data) < JTPHeader.HEADER_SIZE:
                    continue
                    
                header = JTPHeader.unpack(raw_data[:JTPHeader.HEADER_SIZE])
                if header.flags == JTPHeader.FLAG_ACK and header.ack_num == expected_ack_num:
                    # print(f"[<-] Received valid ACK: {header.ack_num}")
                    return True
            except socket.timeout:
                continue
        return False

    def receive_reliable(self):
        """Listens for incoming JTP packets, verifies integrity, and sends ACKs."""
        while True:
            try:
                raw_data, addr = self.sock.recvfrom(2048)
                if len(raw_data) < JTPHeader.HEADER_SIZE:
                    continue

                header_bytes = raw_data[:JTPHeader.HEADER_SIZE]
                payload = raw_data[JTPHeader.HEADER_SIZE:]
                header = JTPHeader.unpack(header_bytes)

                # 1. Cryptographic Integrity Check
                if not header.verify_payload(payload):
                    print(f"[!] Corrupted packet received from {addr}. Dropping.")
                    continue  # Drop packet, sender will timeout and retransmit

                if header.flags == JTPHeader.FLAG_DATA:
                    # print(f"[+] Valid Data Received! Seq: {header.seq_num}. Sending ACK...")
                    # 2. Send Acknowledgment back to sender
                    ack_header = JTPHeader(
                        flags=JTPHeader.FLAG_ACK,
                        window_size=64,
                        seq_num=0,
                        ack_num=header.seq_num + len(payload)
                    )
                    self.sock.sendto(ack_header.pack(), addr)
                    
                    return payload, addr

            except socket.timeout:
                continue # Keep listening
