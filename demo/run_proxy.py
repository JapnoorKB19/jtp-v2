from src.proxy_gateway import LocalProxy

if __name__ == "__main__":
    print("Select Transport Protocol for the Tunnel:")
    print("1. TCP (Standard)")
    print("2. UDP (Standard)")
    print("3. JTP (Custom Proposed Protocol)")
    choice = input("Choice (1/2/3): ").strip()
    
    proto_map = {'1': 'TCP', '2': 'UDP', '3': 'JTP'}
    selected_protocol = proto_map.get(choice, 'JTP')
    
    proxy = LocalProxy(protocol_choice=selected_protocol, tcp_port=8080, target_port=9000)
    proxy.start()

