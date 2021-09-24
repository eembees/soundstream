# coding=utf-8
import socket
import time
from threading import Thread
from queue import Queue

from global_constants_and_functions import *


def initialize_server() -> Tuple[socket.socket, Queue]:
    """
    Initialize a generic UDP server and bind it to the server address.
    Also make a queue and return the socket and queue.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(ADDRESS)
    queue = Queue()
    return sock, queue


class BroadcastThread(Thread):
    """
    The sending thread of the server.
    Iterates through the queue and passes messages to broadcast to clients.
    Keeps track of which clients are communicating with the server.
    """

    def __init__(self, sock: socket.socket, queue: Queue, *args, **kwargs) -> None:
        """Initiate socket and queue from intialize_server() and set the clients to an ampty set"""
        super(BroadcastThread, self).__init__(*args, **kwargs)
        self.sock = sock
        self.queue = queue
        self.clients = set()

    def put_message_in_queue(self, message: Tuple[bytes, int]) -> None:
        """
        This is the method that the receiver should call every time there is a message.
        Should decode the message using decode_message(), check if it is the first message,
            and if it is, add the client to the list of clients.
        Otherwise, add the message to the broadcast queue.
        :param message: message to be decoded by the decode_message method
        """
        # msg, addr = decode_message(message)
        msg, addr = message
        if msg == b"init":
            self.clients.add(addr)
            print(
                datetime.datetime.now().strftime("%H:%M:%S") + f" - Added client {addr}"
            )
        else:
            self.queue.put(message)

    def run(self) -> None:
        """
        Main running method.
        Gets a message from the queue and sends it to all clients.
        Afterwards, sleeps for a short time.
        """
        while True:
            message = self.queue.get()
            self.broadcast_message_to_clients(message)
            time.sleep(SLEEPTIME)

    def broadcast_message_to_clients(self, message: Tuple[bytes, int]):
        """
        Takes a message as input, retrieves origin address and sends the message
        to all clients except original sender.
        """
        # msg, addr = decode_message(message)
        msg, addr = message
        for client in self.clients:
            if client != addr:
                # self.sock.sendto(encode_message(msg), client)
                self.sock.sendto(msg, client)
                print(
                    datetime.datetime.now().strftime("%H:%M:%S")
                    + f" - Sending: {client} <<< {msg[:40]}"
                )


class ReceiverThread(Thread):
    """
    Receiver part of the server.
    Runs in parallel and sends all received messages to be put in the sending queue.
    """

    def __init__(
        self, sock: socket.socket, broadcaster: BroadcastThread, *args, **kwargs
    ):
        """
        Initialize the receiver.
        Socket should be the same as self.broadcaster.sock, unless testing.
        """
        super(ReceiverThread, self).__init__(*args, **kwargs)

        self.broadcaster = broadcaster

        self.sock = self.broadcaster.sock if sock is None else sock

    def start(self) -> None:
        """
        Added start script so we could add the printout.
        Very useful for development and testing.
        """
        super(ReceiverThread, self).start()
        print(
            datetime.datetime.now().strftime("%H:%M:%S")
            + f" - Started receiving messages at {HOST}:{PORT}"
        )

    def run(self) -> None:
        """
        Processes all incoming messages and passes it on to the other thread.
        """
        while True:
            message = self.sock.recvfrom(BUFFERSIZE)
            msg, addr = message
            print(
                datetime.datetime.now().strftime("%H:%M:%S")
                + f" - Received: {addr} >>> {msg[:20]}"
            )
            self.broadcaster.put_message_in_queue(message)


def main():
    """
    Main running loop for this server.
    Gets an initialized server, otherwise, will throw error if address is already in use.
    Could possibly scale with other arguments added.
    """
    server_socket, server_queue = initialize_server()
    thread_broadcast = BroadcastThread(sock=server_socket, queue=server_queue)
    thread_receive = ReceiverThread(sock=server_socket, broadcaster=thread_broadcast)

    thread_broadcast.start()
    thread_receive.start()

    thread_broadcast.join()


if __name__ == "__main__":
    thread_main = Thread(target=main)
    thread_main.start()
    thread_main.join()
