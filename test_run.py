import threading
from src.jtp_socket import JTPSocket

def run_server():
    server = JTPSocket(host='127.0.0.1', port=8080, is_server=True)
    data, addr = server.receive_reliable()
    print(f"\nServer Received: {data.decode()} from {addr}")

def run_client():
    client = JTPSocket()
    message = b"Hello from the custom protocol!"
    client.send_reliable(message, ('127.0.0.1', 8080))
    print("\nClient successfully sent message and received ACK.")

# Run server in a thread so client can connect
threading.Thread(target=run_server, daemon=True).start()
run_client()
