
# JTP V2: Jammu Transport Protocol (Enterprise Architecture)


A custom, secure, and reliable Transport Layer protocol built entirely in user-space over standard UDP datagrams. This project fulfills an advanced networking stack requirement by upgrading to a multi-threaded architecture, implementing complex reliability mechanisms, and enforcing strict cryptographic data integrity.

---

## 🚀 Advanced Features (V2)

Our architecture was completely rewritten for V2 to simulate an enterprise-grade transport layer. The core features include:

* **Multi-Threaded Server Dispatcher:** The JTP Server intercepts all incoming UDP traffic on a single port, parses the source IP/Port, and dynamically spins up isolated worker threads for concurrent `curl` clients, completely preventing sequence number collisions.
* **Go-Back-N Sliding Window:** Upgraded from a basic Stop-and-Wait ARQ. The protocol now transmits multiple in-flight packets simultaneously (Window Size: 5) and actively listens for cumulative acknowledgments, maximizing network pipeline utilization.
* **Formal State Machine (FIN/ACK Teardown):** Replaced unstable timeout-based closures with a graceful 4-way handshake. The sockets track states (`ESTABLISHED`, `FIN_WAIT`, `CLOSED`) to ensure all data is mathematically verified before safely tearing down the connection.
* **Zero-Trust Cryptographic Integrity:** Standard UDP checksums are disabled. JTP actively calculates a truncated SHA-256 hash of the payload and embeds it directly into the custom header, silently dropping any packets that have been tampered with or corrupted in transit.
* **Dynamic Application Tunneling:** Includes a local proxy gateway that intercepts real-world HTTP traffic (`curl`) and allows the user to instantly toggle the transport layer between **TCP**, standard **UDP**, and our custom **JTP**.

---

## 📂 Detailed Project Structure

```text
jtp-v2/
├── src/                          # Core Protocol Architecture
│   ├── jtp_header.py             # Defines the 22-byte structure, bitwise flags, and SHA-256 hashing logic.
│   ├── jtp_socket.py             # The V2 Engine: Contains both the Multi-threaded Server Dispatcher and the Go-Back-N Socket object.
│   └── proxy_gateway.py          # The intercept layer that tunnels raw HTTP requests into the selected transport protocol.
│
├── benchmarks/                   # Performance Testing Suite
│   └── run_benchmark.py          # Transmits a 1.00 MB payload across TCP, UDP, and JTP to calculate exact MB/s throughput and overhead constraints.
│
├── demo/                         # Execution Scripts
│   ├── web_server.py             # The backend HTTP application that serves web pages through our custom transport layer.
│   └── run_proxy.py              # The user-facing script to boot the proxy and select the tunneling protocol.
│
└── docs/                         # Evidence and Documentation
    └── jtp_v2_capture.pcap       # Live Wireshark loopback capture proving header byte-alignment and the FIN/ACK state machine.
```

---

## 🛠️ Usage Instructions

### 1. Boot the Multi-Protocol Demo
You will need three separate terminal instances to simulate the network.

**Terminal 1 (Backend Server):**
```bash
python3 -m demo.web_server
# -> Select Option 3 to boot the JTP V2 Dispatcher
```

**Terminal 2 (Local Proxy Gateway):**
```bash
python3 -m demo.run_proxy
# -> Select Option 3 to lock the tunnel to JTP
```

**Terminal 3 (The Client):**
```bash
curl -v http://localhost:8080
```

---

## 🔍 Wireshark Verification (WSL Integration)

To mathematically prove the protocol's architecture, we capture the loopback traffic.

**1. Start the Capture:**
```bash
sudo tcpdump -i lo udp port 9000 -w docs/jtp_v2_capture.pcap
```
**2. Trigger the Traffic:** Run your `curl` command through the proxy.
**3. Stop the Capture:** Press `Ctrl+C` in the tcpdump terminal.
**4. Launch Wireshark directly from the WSL Terminal:**
```bash
"/mnt/c/Program Files/Wireshark/Wireshark.exe" docs/jtp_v2_capture.pcap
```
*(Inspect the hex dump of the UDP payload to visually verify the 22-byte header boundary, the SHA-256 signature, and the `0x04` FIN flag during teardown).*

---

## 📊 Technical Specifications & Benchmarks

JTP encapsulates application data within a highly structured 22-byte binary header:

| Offset | Field | Size | Description |
| :--- | :--- | :--- | :--- |
| `0x00` | **Flags** | 1 Byte | `0x00` DATA, `0x01` ACK, `0x02` SYN, `0x04` FIN |
| `0x01` | **Window** | 1 Byte | Flow control buffer limit |
| `0x02` | **Seq Num** | 4 Bytes | Byte offset tracking |
| `0x06` | **Ack Num** | 4 Bytes | Next expected sequence number |
| `0x0A` | **Length** | 2 Bytes | Size of encapsulated application data |
| `0x0C` | **Hash** | 10 Bytes | Truncated SHA-256 signature |

To run the comparative performance benchmark suite:
```bash
python3 -m benchmarks.run_benchmark
```

## 📝 Architectural Conclusion

JTP V2 demonstrates a clear architectural trade-off between pure OS-level performance and zero-trust security. While it successfully bridges the gap by providing TCP-like connection states and multi-threaded reliability over UDP, the user-space Python GIL (Global Interpreter Lock) becomes a natural bottleneck when calculating heavy cryptographic hashes for every packet. It proves that while Python is excellent for prototyping complex protocol logic, maximum throughput for cryptographic pipelines requires kernel-level C implementations.
```
