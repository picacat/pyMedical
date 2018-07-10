
import socket
from PyQt5 import QtCore


class UDPSocketServer(QtCore.QThread):
    update_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(UDPSocketServer, self).__init__(parent)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.buffer_size = 1024
        self._init_socket_server()

    def __del__(self):
        self.server.close()
        self.wait()

    def _init_socket_server(self):
        host = ''
        port = 8888
        server_address = (host, port)
        self.server.bind(server_address)

    def run(self):
        while True:
            data, client_address = self.server.recvfrom(self.buffer_size)
            self.update_signal.emit(str(data, 'utf-8'))
            self.server.sendto(data, client_address)
