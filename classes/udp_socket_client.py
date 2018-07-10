
import socket


class UDPSocketClient:
    def __init__(self, parent=None):
        # super(UDPSocketClient, self).__init__(parent)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.buffer_size = 1024
        self._init_socket_client()

    def _init_socket_client(self):
        host = '255.255.255.255'
        port = 8888
        self.server_address = (host, port)

    def send_data(self, data):
        self.client.sendto(bytes(data, 'utf-8'), self.server_address)
        received_data, address = self.client.recvfrom(self.buffer_size)
