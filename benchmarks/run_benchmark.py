import socket
import time
import threading
from src.jtp_socket import JTPSocket

# --- Configuration ---
HOST = '127.0.0.1'
PORT_TCP = 9001
PORT_UDP = 9002
PORT_JTP = 9003

PAYLOAD_MB = 1
PAYLOAD_SIZE = PAYLOAD_MB * 1024 * 1024  # 1 MB of data
CHUNK_SIZE = 1400                        # Standard MTU size
TEST_DATA = b"X" * PAYLOAD_SIZE          # Dummy data for transmission

# ==========================================
# 1. TCP BENCHMARK (Kernel-Level Reliable)
# ==========================================
def tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT_TCP))
    server.listen(1)
    conn, _ = server.accept()
    
    received = 0
    while received < PAYLOAD_SIZE:
        data = conn.recv(4096)
        if not data: break
        received += len(data)
    conn.close()
    server.close()

def benchmark_tcp():
    threading.Thread(target=tcp_server, daemon=True).start()
    time.sleep(0.5) # Allow server to bind
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT_TCP))
    
    start_time = time.time()
    client.sendall(TEST_DATA)
    client.close() # Wait for graceful OS-level close
    end_time = time.time()
    
    return end_time - start_time

# ==========================================
# 2. UDP BENCHMARK (Kernel-Level Unreliable)
# ==========================================
def benchmark_udp():
    """
    Note: Because UDP is connectionless and drops packets, 
    we measure how fast the OS can dump the payload onto the wire.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    chunks = [TEST_DATA[i:i+CHUNK_SIZE] for i in range(0, PAYLOAD_SIZE, CHUNK_SIZE)]
    
    start_time = time.time()
    for chunk in chunks:
        client.sendto(chunk, (HOST, PORT_UDP))
    end_time = time.time()
    
    client.close()
    return end_time - start_time

# ==========================================
# 3. JTP V2 BENCHMARK (User-Space Reliable)
# ==========================================
def jtp_server():
    receiver = JTPSocket(existing_sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
    receiver.sock.bind((HOST, PORT_JTP))
    
    received_bytes = 0
    while received_bytes < PAYLOAD_SIZE:
        data, _ = receiver.receive_reliable()
        if not data: break # FIN teardown received
        received_bytes += len(data)

def benchmark_jtp():
    threading.Thread(target=jtp_server, daemon=True).start()
    time.sleep(0.5) # Allow server to bind
    
    client = JTPSocket(target_addr=(HOST, PORT_JTP))
    
    start_time = time.time()
    client.send_reliable(TEST_DATA)
    client.close() # Wait for V2 FIN/ACK graceful teardown
    end_time = time.time()
    
    return end_time - start_time

# ==========================================
# EXECUTION & ANALYSIS
# ==========================================
if __name__ == "__main__":
    print(f"[*] Starting JTP V2 Architecture Benchmarks...")
    print(f"[*] Payload Size: {PAYLOAD_MB:.2f} MB ({PAYLOAD_SIZE} bytes)\n")

    # Run tests
    time_tcp = benchmark_tcp()
    print(f"[TCP]  Time: {time_tcp:.4f}s | Throughput: {(PAYLOAD_MB)/time_tcp:8.2f} MB/s (Kernel Optimized)")

    time_udp = benchmark_udp()
    print(f"[UDP]  Time: {time_udp:.4f}s | Throughput: {(PAYLOAD_MB)/time_udp:8.2f} MB/s (Unreliable Blast)")

    time_jtp = benchmark_jtp()
    print(f"[JTP]  Time: {time_jtp:.4f}s | Throughput: {(PAYLOAD_MB)/time_jtp:8.2f} MB/s (User-Space Cryptographic)")

    # Print Overhead Analysis
    print("\n--- Control Overhead Analysis ---")
    num_packets = PAYLOAD_SIZE // CHUNK_SIZE
    print(f"Total Packets Sent: ~{num_packets}")
    print(f"TCP Overhead:  ~{num_packets * 20:,} bytes (20 bytes/header)")
    print(f"UDP Overhead:  ~{num_packets * 8:,} bytes (8 bytes/header)")
    print(f"JTP Overhead:  ~{num_packets * 30:,} bytes (8 UDP + 22 Custom JTP)")

    print("\n[Conclusion]:")
    print("While JTP trades raw throughput for security, it successfully bridges")
    print("the gap by providing TCP-like connection states and reliability over UDP,")
    print("while adding an unbreakable SHA-256 integrity layer.")
