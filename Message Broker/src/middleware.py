"""Middleware to communicate with PubSub Message Broker."""
from enum import Enum
import socket
import json
import pickle
import xml.etree.ElementTree as ET
from src.protocolo import *
import logging

class MiddlewareType(Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2

class Queue:
    """Representation of Queue interface for both Consumers and Producers."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        self.topic = topic
        self.type = _type
        
        self._host = "localhost"
        self._port = 5000
        self.mid_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mid_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mid_sock.connect((self._host, self._port))

        serializer = 'json' if isinstance(self, JSONQueue) else 'xml' if isinstance(self, XMLQueue) else 'pickle'
        connect_msg = ConnectMessage(serializer)
        MBProto.send_msg(self.mid_sock, connect_msg, QueueType.JSON)
        logging.info(f"Connected to broker with serializer {serializer}")

        # Subscribe to topic
        subscribe_msg = SubscribeMessage(topic)
        MBProto.send_msg(self.mid_sock, subscribe_msg, self.queue_type())
        logging.info(f"Subscribed to topic {topic} with serializer {serializer}")

    def queue_type(self):
        """Returns the QueueType based on the instance."""
        if isinstance(self, JSONQueue):
            return QueueType.JSON
        elif isinstance(self, XMLQueue):
            return QueueType.XML
        elif isinstance(self, PickleQueue):
            return QueueType.PICKLE

    def push(self, value):
        """Sends data to the broker using the specific serialization."""
        msg = PublishMessage(self.topic, value)
        MBProto.send_msg(self.mid_sock, msg, self.queue_type())
        logging.info(f"Pushed message {value} to topic {self.topic}")

    def pull(self):
        """Pulls data from the broker using the specific serialization."""
        response = MBProto.recv_msg(self.mid_sock)
        logging.info(f"Pulled message {response} from topic {self.topic}")
        if response:
            return response['topic'], response['message']
        return None, None


    def list_topics(self):
        """Lists all topics available in the broker."""
        list_msg = ListMessage()
        MBProto.send_msg(self.mid_sock, list_msg, self.queue_type())
        return MBProto.recv_msg(self.mid_sock)

    def cancel(self):
        """Cancel subscription."""
        unsubscribe_msg = UnsubscribeMessage(self.topic)
        MBProto.send_msg(self.mid_sock, unsubscribe_msg, self.queue_type())
        logging.info(f"Cancelled subscription to topic {self.topic}")

class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)

class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)

class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)
