
import socket
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox

from libs import system_utils


class UDPSocketServer(QtCore.QThread):
    update_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(UDPSocketServer, self).__init__(parent)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.buffer_size = 1024
        self.socket_connected = False
        self._init_socket_server()

    def __del__(self):
        self.server.close()
        self.wait()

    def _init_socket_server(self):
        host = ''
        port = 8888
        server_address = (host, port)
        try:
            self.server.bind(server_address)
            self.socket_connected = True
        except OSError:
            pass
            # system_utils.show_message_box(
            #    QMessageBox.Critical,
            #    '驅動網路Socket失敗',
            #    '<h3>無法驅動網路Socket功能, 所有的廣播訊息將無法接收.</h3>',
            #    '請確定是否有其他的醫療系統正在使用中.'
            # )

    def connected(self):
        return self.socket_connected

    def run(self):
        while True:
            try:
                data, client_address = self.server.recvfrom(self.buffer_size)
            except OSError:
                # QtWidgets.QApplication.exit(0)
                break

            self.update_signal.emit(str(data, 'utf-8'))
            self.server.sendto(data, client_address)
