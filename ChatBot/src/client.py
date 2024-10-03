"""CD Chat client program"""
import logging
import sys
import socket
import selectors
import fcntl
import os

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)

class Client:
    def __init__(self, name: str = "Foo"):
        self.name = name
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()
        self.channel = "None"  
        self.CDP = CDProto()

    def connect(self):
        self.s.connect(('127.0.0.1',6666))
        self.selector.register(self.s, selectors.EVENT_READ, self.read)
        self.s.setblocking(False)
        # Registro no servidor
        registerMessage = self.CDP.register(self.name)
        self.CDP.send_msg(self.s, registerMessage)

    def read(self, sock, mask):
        msg = self.CDP.recv_msg(self.s)
        if msg.command == "message":
            print(f"{msg.message}")

    def getInputFromKeyboard(self, stdin, mask):

        msg = stdin.readline().strip()  # Remover espaços e quebras de linha

        if msg != "":

            if msg == "exit":
                # Fecha a conexão do socket deste cliente específico
                self.s.close()
                sys.exit(f">> {self.name} saiu do chat.")

            elif msg.startswith("/join "):
                commands = msg.split(' ')

                if len(commands) != 2:
                    print(">> Nome do Canal Inválido. Use /join <nome_do_canal>")

                else:
                    self.channel = commands[1]
                    joinMessage = self.CDP.join(self.channel)
                    self.CDP.send_msg(self.s, joinMessage)

                    print(f">> {self.name} entrou no canal {self.channel}.")


            else:
                
                sendMessage = self.CDP.message(msg, self.channel)
                self.CDP.send_msg(self.s, sendMessage)

        else:
            print("Mensagem Vazia")



    def loop(self):
        """Loop indefinetely."""
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        self.selector.register(sys.stdin, selectors.EVENT_READ, self.getInputFromKeyboard)

        while True:
            sys.stdout.write(f'({self.channel})> ')
            sys.stdout.flush()
            for k, mask in self.selector.select():
                callback = k.data
                callback(k.fileobj, mask)
