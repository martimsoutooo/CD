"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket


class Message:
    """Message Type."""
    def __init__(self,command):
        self.command = command

    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self, channel):
        super().__init__(command = "join")
        self.channel = channel        
    
    def __str__(self):
        return f"{{\"command\": \"{self.command}\", \"channel\": \"{self.channel}\"}}"


class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, user):
        super().__init__(command = "register")
        self.user = user
    
    def __str__(self):
        return f"{{\"command\": \"{self.command}\", \"user\": \"{self.user}\"}}"
    

    
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self,message, channel, ts=None):
        super().__init__(command="message")
        self.message = message
        self.channel = channel
        self.ts = ts if ts is not None else int(datetime.now().timestamp())

    def __str__(self):
        base = f'{{"command": "{self.command}", "message": "{self.message}", "ts": {self.ts}'
        if self.channel is not None:
            return base + f', "channel": "{self.channel}"}}'
        return base + '}'


        


class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage(username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage(channel)

    @classmethod
    def message(cls, message: str,channel: str = None) -> TextMessage:
        """Creates a TextMessage object with current timestamp."""
        return TextMessage(message, channel)


    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        json_msg = str(msg).encode("utf-8")
        json_msg_len = len(json_msg).to_bytes(2,"big")
        connection.sendall(json_msg_len + json_msg)
        
    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""

        try:
            msg_len = int.from_bytes(connection.recv(2), "big")
            dic_json = connection.recv(msg_len)

            dic_json = json.loads(dic_json.decode("utf-8"))
        except:
            raise CDProtoBadFormat(dic_json)
        
        if dic_json["command"] == "join":
            return JoinMessage(dic_json["channel"])
        elif dic_json["command"] == "register":
            return RegisterMessage(dic_json["user"])
        elif dic_json["command"] == "message":
            if "channel" not in dic_json.keys():
                return TextMessage(dic_json["message"], None, dic_json["ts"])
            else:
                return TextMessage(dic_json["message"], dic_json["channel"], dic_json["ts"])
            

        
class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
