"""CD Chat server program."""
import logging
import selectors
import socket 


logging.basicConfig(filename="server.log", level=logging.DEBUG)
from .protocol import CDProto, CDProtoBadFormat

class Server:
    """Chat Server process."""

    def __init__(self):
        """Initialize the server."""
        self.selector = selectors.DefaultSelector()  # Criar o selector
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Criar o socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('localhost', 6666))   # Ligar o socket a um endereço

        print("Server started")

        self.s.listen(5)    # Limite de clientes
        self.selector.register(self.s, selectors.EVENT_READ, self.accept)
        self.infUsers = {}  # Dicionário para armazenar informações dos clientes conectados

    def accept(self, sock, mask):
        """Accept a new connection."""
        conn, addr = sock.accept()
        self.selector.register(conn, selectors.EVENT_READ, self.read)
        

    def read(self, conn, mask):
        """Read from the socket."""

        try:
            msg = CDProto.recv_msg(conn)
        except CDProtoBadFormat:
            msg = None
        
        if msg:
            if msg.command == "register":
                print(f'>> {msg.user} entrou no servidor')
                # Inicializa o cliente no canal "None"
                self.infUsers[conn] = {"user": msg.user, "channels": {"None"}}
            
            elif msg.command == "join":
                # Atualiza os canais do cliente, adicionando-o ao novo canal e removendo de "None" 
                self.infUsers[conn]["channels"].add(msg.channel)
                print(f'>> {self.infUsers[conn]["user"]} entrou no canal {msg.channel}')

            elif msg.command == "message":
                
                channel = msg.channel
                broadcast_msg = f"({self.infUsers[conn]['user']}): {msg.message}" 
                msg = CDProto.message(broadcast_msg, channel)

                print(f'>> {self.infUsers[conn]["user"]} enviou mensagem para o canal {channel}')
                # Envia a mensagem para todos os usuários no mesmo canal
                for client_conn, info in self.infUsers.items():
                    if channel in info["channels"] and client_conn != conn:  # Não envia de volta ao remetente
                        CDProto.send_msg(client_conn, msg)
        else:
            
            print(f">> {self.infUsers[conn]['user']} desconectou-se")

            self.infUsers.pop(conn, None)  # Remove o usuário das informações do servidor
            self.selector.unregister(conn)  # Remove do seletor
            conn.close()  # Fecha a conexão


    def loop(self):
        """Loop indefinetely."""

        while True:
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
