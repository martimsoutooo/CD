import selectors
import socket
import json
import enum
from typing import Dict, List, Tuple
from src.protocolo import *
import logging
import threading

logging.basicConfig(level=logging.DEBUG)

class Serializer(enum.Enum):
    """Possible message serializers."""
    JSON = 0
    XML = 1
    PICKLE = 2

class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""

        logging.basicConfig(level=logging.DEBUG)

        self.canceled = False
        self._host = "localhost"
        self._port = 5000

        # Socket configuration
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self._host, self._port))
        self.sock.listen(100)
        
        # Selector configuration
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.sock, selectors.EVENT_READ, self.accept)
        
        # Data structures
        self.lock = threading.Lock()
        self.subscriptions = {}
        self.topics = {}
        self.sockets = {}

        logging.info("Broker initialized")

    def list_topics(self) -> List[str]:
        """Send list of all topics to a requester."""
        return [topic for topic in self.topics]

    def get_topic(self, topic):
        """Get a message from a topic."""
        for top,values in self.topics.items():
            if topic.startswith(top):
                if values:
                    return values[-1]

        return None
    
    def put_topic(self, topic, value):
        """Put a message in a topic."""
        if topic not in self.topics:
            self.topics[topic] = [value]
        else:
            self.topics[topic].append(value)
        logging.debug(f"Message {value} put in topic {topic}")
        
    def list_subscriptions(self, topic: str) -> List[Tuple[socket.socket, Serializer]]:
        """List all subscriptions for a topic."""
        return self.subscriptions.get(topic, [])
    
    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        logging.debug(f"Trying to subscribe {address.getpeername()} to {topic} with format {_format}")
        if topic not in self.subscriptions:
            self.subscriptions[topic] = [(address, _format)]
            logging.info(f"Subscribed new socket to new topic '{topic}'. Total subscriptions: {len(self.subscriptions[topic])}")
        else:
            # Checking explicitly if the tuple (address, _format) is already in the list to avoid duplicates
            if (address, _format) not in self.subscriptions[topic]:
                self.subscriptions[topic].append((address, _format))
                logging.info(f"Subscribed new socket to existing topic '{topic}'. Total subscriptions: {len(self.subscriptions[topic])}")
            else:
                logging.warning(f"Attempt to re-subscribe {address.getpeername()} to {topic} with format {_format} was ignored.")

    def unsubscribe(self, topic, address):
        """Unsubscribe a socket from a topic."""
        if topic in self.subscriptions:
            self.subscriptions[topic] = [(sub, fmt) for sub, fmt in self.subscriptions[topic] if sub != address]
            logging.info(f"Unsubscribed {address.getpeername()} from {topic}")
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]

    def publish(self, topic, data):
        message = PublishMessage(topic, data)
        self.put_topic(topic, data)
        logging.debug(f"Publishing message {data} to topic {topic}")
        subscriptions = self.list_subscriptions(topic)
        if not subscriptions:
            logging.info(f"No subscribers for topic {topic}")
        for sub, fmt in subscriptions:
            try:
                MBProto.send_msg(sub, message, fmt)
                logging.info(f"Sent message {data} to {sub.getpeername()}")
            except ConnectionResetError:
                logging.error(f"Connection reset by peer {sub.getpeername()}")
                self.cleanup_connections(sub)

    def accept(self, sock, mask):
        """Accept new connection."""
        conn, addr = sock.accept()
        self.selector.register(conn, selectors.EVENT_READ, self.read)
        logging.info(f"Accepted connection from {addr}")


    def read(self, conn, mask):
        message = MBProto.recv_msg(conn)
        if message:
            logging.info(f"Received message: {message}")
            try:
                if not isinstance(message, dict):
                    message = message.dict()
                command = message.get('command')
                if command == 'subscribe':
                    self.subscribe(message['topic'], conn, Serializer[message.get('serializer', 'JSON')])
                elif command == 'unsubscribe':
                    self.unsubscribe(message['topic'], conn)
                elif command == 'publish':
                    self.publish(message['topic'], message['message'])
                elif command == 'list':
                    topics = self.list_topics()
                    list_response = ListResponseMessage(topics)
                    MBProto.send_msg(conn, list_response, QueueType.JSON)
                elif command == 'connect':
                    self.sockets[conn] = message['serializer']
            except AttributeError as e:
                logging.error(f"Invalid message: {e}")
        else:
            self.cleanup_connections(conn)


    def cleanup_connections(self, conn):
        """Cleanup connection."""
        self.selector.unregister(conn)
        conn.close()
        for subs in self.subscriptions.values():
            if conn in [sub[0] for sub in subs]:
                subs[:] = [sub for sub in subs if sub[0] != conn]
        logging.info(f"Cleaned up connection")

    def run(self):
        """Run the broker until canceled."""
        while not self.canceled:
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
