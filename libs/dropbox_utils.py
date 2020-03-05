# download api 2020.02.10

#coding: utf-8
from PyQt5 import QtCore

import urllib
from threading import Thread
from queue import Queue

from libs import dialog_utils


def _download_file_thread(out_queue, download_file_name, url):
    QtCore.QCoreApplication.processEvents()

    u = urllib.request.urlopen(url)
    data = u.read()
    u.close()
    with open(download_file_name, "wb") as f:
        f.write(data)

    out_queue.put(download_file_name)


# 取得安全簽章
def download_dropbox_file(file_name, url, title, message, hint):
    msg_box = dialog_utils.message_box(title, message, hint)
    msg_box.show()

    msg_queue = Queue()
    QtCore.QCoreApplication.processEvents()

    t = Thread(target=_download_file_thread, args=(msg_queue, file_name, url))
    t.start()
    download_file_name = msg_queue.get()
    msg_box.close()

    return download_file_name
