# JTP: Jammu Transport Protocol

A custom, secure, and reliable Transport Layer protocol built over standard UDP. This project fulfills a complete networking stack requirement by implementing reliability mechanisms (Stop-and-Wait ARQ) and cryptographic data integrity (SHA-256) in user space.

## 🚀 Key Features

* **Custom Segment Architecture:** A specialized 22-byte header for sequencing and hashing.
* **Reliability:** Implements timeouts and retransmissions for guaranteed delivery over UDP.
* **Cryptographic Integrity:** SHA-256 payload hashing to prevent data tampering.
* **Protocol Choice:** A proxy-integrated application allowing users to toggle between **TCP**, **UDP**, and **JTP**.
* **Terminal Integration:** Full support for `curl` tunneling through the custom transport stack.

---

## 📂 Project Structure

```
jtp-project/
├── src/
│   ├── jtp_header.py
│   ├── jtp_socket.py
│   └── proxy_gateway.py
├── benchmarks/
│   └── run_benchmark.py
├── demo/
│   ├── web_server.py
│   └── run_proxy.py
└── docs/
    └── jtp_demo.pcap
```

---

## 🛠️ Usage Instructions

### 1. Multi-Protocol Demo

**Terminal 1 (Backend Server):**

```bash
python3 -m demo.web_server
```

**Terminal 2 (Local Proxy):**

```bash
python3 -m demo.run_proxy
```

**Terminal 3 (Client):**

```bash
curl -v http://localhost:8080
```

---

### 2. Performance Benchmarking

```bash
python3 -m benchmarks.run_benchmark
```

---

### 3. Wireshark Analysis

1. Start tcpdump:

```bash
sudo tcpdump -i lo udp port 9000 -w docs/jtp_demo.pcap
```

2. Run the demo
3. Open `.pcap` in Wireshark

---

## 📊 Technical Specifications

* **Flags (1B):** Packet type (SYN/ACK/DATA/FIN)
* **Window (1B):** Flow control
* **Seq/Ack (8B):** Reliability
* **Integrity Hash (10B):** Truncated SHA-256

---

## 📝 Conclusion

JTP demonstrates a trade-off between performance and reliability by implementing guaranteed delivery and cryptographic integrity over UDP.
