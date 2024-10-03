import json
import struct
import xml.etree.ElementTree as ET
import pickle
import socket
from enum import Enum, unique

@unique
class QueueType(Enum):
    JSON = 1
    XML = 2
    PICKLE = 3

class Message:
    """Base Message Type."""
    
    def __init__(self, command):
        self.command = command
    
    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

    def __repr__(self):
        return str(self)

    def get_command(self):
        return self.command

class ConnectMessage(Message):
    def __init__(self, serializer):
        super().__init__("connect")
        self.serializer = serializer

    def dict(self):
        return {
            'command': self.command,
            'serializer': self.serializer
        }

class SubscribeMessage(Message):
    def __init__(self, topic):
        super().__init__("subscribe")
        self.topic = topic

    def dict(self):
        return {
            'command': self.command,
            'topic': self.topic
        }

class UnsubscribeMessage(Message):
    def __init__(self, topic):
        super().__init__("unsubscribe")
        self.topic = topic

    def dict(self):
        return {
            'command': self.command,
            'topic': self.topic
        }

class PublishMessage(Message):
    def __init__(self, topic, message):
        super().__init__("publish")
        self.topic = topic
        self.message = message

    def dict(self):
        return {
            'command': self.command,
            'topic': self.topic,
            'message': self.message
        }

class ListMessage(Message):
    def __init__(self):
        super().__init__("list")

    def dict(self):
        return {
            'command': self.command
        }

class ListResponseMessage(Message):
    def __init__(self, topic_list):
        super().__init__("list")
        self.topicList = topic_list

    def dict(self):
        return {
            'command': self.command,
            'topicList': self.topicList
        }

class MBProto:
    """Message Broker Protocol."""
    
    @staticmethod
    def send_msg(connection: socket, msg: Message, queue: QueueType):
        """Encodes and sends a message object based on the QueueType."""
        if queue == QueueType.JSON:
            MBProto.send_json(connection, msg)
        elif queue == QueueType.XML:
            MBProto.send_xml(connection, msg)
        elif queue == QueueType.PICKLE:
            MBProto.send_pickle(connection, msg)
    
    @staticmethod
    def send_json(connection: socket, msg: Message):
        encoded_msg = json.dumps(msg.__dict__).encode('utf-8')
        MBProto._send_prepared_message(connection, encoded_msg, QueueType.JSON)
    
    @staticmethod
    def send_xml(connection: socket, msg: Message):
        root = ET.Element('Message')
        for key, value in msg.__dict__.items():
            ET.SubElement(root, key).text = str(value)
        encoded_msg = ET.tostring(root)
        MBProto._send_prepared_message(connection, encoded_msg, QueueType.XML)
    
    @staticmethod
    def send_pickle(connection: socket, msg: Message):
        encoded_msg = pickle.dumps(msg)
        MBProto._send_prepared_message(connection, encoded_msg, QueueType.PICKLE)
    
    @staticmethod
    def _send_prepared_message(connection: socket, data: bytes, queue_type: QueueType):
        header = struct.pack('!BB', len(data), queue_type.value)
        connection.send(header + data)

    @staticmethod
    def recv_msg(connection: socket):
        """Receives a message object and decodes based on QueueType."""
        try:
            header = connection.recv(2)
            if not header:
                return None
            msg_len, queue_type_val = struct.unpack('!BB', header)
            data = b''
            while len(data) < msg_len:
                packet = connection.recv(msg_len - len(data))
                if not packet:
                    return None
                data += packet
            queue_type = QueueType(queue_type_val)
            if queue_type == QueueType.JSON:
                return MBProto.recv_json(data)
            elif queue_type == QueueType.XML:
                return MBProto.recv_xml(data)
            elif queue_type == QueueType.PICKLE:
                return MBProto.recv_pickle(data)
        except Exception as e:
            print(f"Error receiving message: {str(e)}")
            return None
        
    @staticmethod
    def recv_json(data):
        return json.loads(data.decode('utf-8'))
    
    @staticmethod
    def recv_xml(data):
        tree = ET.fromstring(data)
        return {child.tag: child.text for child in tree}
    
    @staticmethod
    def recv_pickle(data):
        return pickle.loads(data)
    
class MBProtoBadFormat(Exception):
    """Exception for invalid message format."""
    def __init__(self, message=""):
        self.message = message

    def __str__(self):
        return f"MBProtoBadFormat: {self.message}"
