# 元件設定 2017.09.26

#coding: utf-8
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname("__file__")))
CSS_PATH = "css"


def get_css_file():
    if sys.platform == 'win32':
        return 'style.win32.css'
    else:
        return 'style.css'


def set_css(widget):
    css_file = os.path.join(BASE_DIR, CSS_PATH, get_css_file())
    widget.setStyleSheet(open(css_file, "r").read())


# 設定主題
def set_theme(ui, settings):
    style = settings.field('外觀主題')
    if style is None:
        style = 'Fusion'

    ui.setStyle(QtWidgets.QStyleFactory.create(style))


def show_message_box(message_icon, title, text, informative):
    msg_box = QMessageBox()
    msg_box.setIcon(message_icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setInformativeText(informative)
    msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
    msg_box.exec_()
