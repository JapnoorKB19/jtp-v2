import socket
import time
import threading
from src.jtp_socket import JTPSocket

# Constants for the test
PAYLOAD_SIZE = 1024 * 1024  # 1 MB of random data
CHUNK_SIZE = 1400           # Standard MTU-safe chunk
TEST_DATA = b'x' * PAYLOAD_SIZE
HOST = '127.0.0.1'
PORT_TCP = 8001
PORT_UDP = 8002
PORT_JTP = 8003

# --- 1. TCP Benchmark ---
def tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT_TCP))
    server.listen(1)
    conn, _ = server.accept()
    received = 0
    while received < PAYLOAD_SIZE:
        data = conn.recv(CHUNK_SIZE)
        if not data: break
        received += len(data)
    conn.close()
    server.close()

def benchmark_tcp():
    threading.Thread(target=tcp_server, daemon=True).start()
    time.sleep(0.5) # Give server time to start
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT_TCP))
    
    start_time = time.time()
    client.sendall(TEST_DATA)
    end_time = time.time()
    
    client.close()
    return end_time - start_time

# --- 2. Standard UDP Benchmark (Unreliable) ---
def udp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT_UDP))
    received = 0
    # UDP might drop packets, so we just wait a brief moment
    server.settimeout(1.0) 
    try:
        while received < PAYLOAD_SIZE:
            data, _ = server.recvfrom(2048)
            received += len(data)
    except socket.timeout:
        pass
    server.close()

def benchmark_udp():
    threading.Thread(target=udp_server, daemon=True).start()
    time.sleep(0.5)
    
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    chunks = [TEST_DATA[i:i+CHUNK_SIZE] for i in range(0, len(TEST_DATA), CHUNK_SIZE)]
    
    start_time = time.time()
    for chunk in chunks:
        client.sendto(chunk, (HOST, PORT_UDP))
    end_time = time.time()
    
    client.close()
    return end_time - start_time

# --- 3. JTP Benchmark (Our Custom Reliable UDP) ---
def jtp_server():
    server = JTPSocket(host=HOST, port=PORT_JTP, is_server=True)
    received = 0
    # JTP is reliable, so we wait until we get all the data
    while received < PAYLOAD_SIZE:
        data, _ = server.receive_reliable()
        received += len(data)

def benchmark_jtp():
    threading.Thread(target=jtp_server, daemon=True).start()
    time.sleep(0.5)
    
    client = JTPSocket()
    
    start_time = time.time()
    client.send_reliable(TEST_DATA, (HOST, PORT_JTP))
    end_time = time.time()
    
    return end_time - start_time

# --- Runner and Math ---
if __name__ == "__main__":
    print(f"[*] Starting Benchmarks... Payload: {PAYLOAD_SIZE / 1024 / 1024:.2f} MB\n")
    
    time_tcp = benchmark_tcp()
    print(f"[TCP]  Time: {time_tcp:.4f}s | Throughput: {(PAYLOAD_SIZE/1024/1024)/time_tcp:.2f} MB/s")
    
    time_udp = benchmark_udp()
    print(f"[UDP]  Time: {time_udp:.4f}s | Throughput: {(PAYLOAD_SIZE/1024/1024)/time_udp:.2f} MB/s (Unreliable)")
    
    time_jtp = benchmark_jtp()
    print(f"[JTP]  Time: {time_jtp:.4f}s | Throughput: {(PAYLOAD_SIZE/1024/1024)/time_jtp:.2f} MB/s")

    print("\n--- Control Overhead Analysis ---")
    num_packets = PAYLOAD_SIZE // CHUNK_SIZE
    print(f"Total Packets Sent: ~{num_packets}")
    print(f"TCP Overhead:  ~{num_packets * 20} bytes (20 bytes/header)")
    print(f"UDP Overhead:  ~{num_packets * 8} bytes (8 bytes/header)")
    print(f"JTP Overhead:  ~{num_packets * 30} bytes (8 UDP + 22 Custom JTP bytes/header)")
    
    print("\n[Conclusion]: JTP provides TCP-like reliability and security hashes, but naturally incurs higher overhead and latency due to application-layer stop-and-wait ACKs in Python.")
