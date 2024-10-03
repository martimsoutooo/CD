import argparse
import threading
from http_server import run_http_server
from p2p_server import P2PServer

class Node:
    def __init__(self, http_port, p2p_port, network_address=None):
        self.http_port = http_port
        self.p2p_port = p2p_port
        self.network_address = network_address
        self.p2p_server = P2PServer(p2p_port, known_nodes=[network_address] if network_address else [])

    def start(self):
        self.p2p_server.start()
        threading.Thread(target=run_http_server, args=(self.http_port, self.p2p_server)).start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="Porto HTTP do nó", type=int, default=8000)
    parser.add_argument("-s", help="Porto do protocolo P2P do nó", type=int, required=True)
    parser.add_argument("-a", help="Endereço e porto do nó na rede P2P a que se pretende juntar", required=False)
    args = parser.parse_args()

    address = args.a.split(":") if args.a else None
    network_address = (address[0], int(address[1])) if address else None

    node = Node(http_port=args.p, p2p_port=args.s, network_address=network_address)
    node.start()
