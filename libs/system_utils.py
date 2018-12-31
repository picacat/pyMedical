# 元件設定 2017.09.26

#coding: utf-8
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname("__file__")))
CSS_PATH = "css"


def get_css_file(system_settings):
    css_file = 'style'

    if system_settings.field('外觀顏色') == '紅色':
        css_file += '.red'
    elif system_settings.field('外觀顏色') == '綠色':
        css_file += '.green'
    elif system_settings.field('外觀顏色') == '藍色':
        css_file += '.blue'
    elif system_settings.field('外觀顏色') == '灰色':
        css_file += '.gray'

    if sys.platform == 'win32':
        css_file += '.win32'

    css_file += '.css'

    return css_file


def get_font():
    if sys.platform == 'win32':
        font = "Microsoft JhengHei"
    else:
        font = 'Noto Sans Mono'

    return font


def set_css(widget, system_settings):
    css_file = os.path.join(BASE_DIR, CSS_PATH, get_css_file(system_settings))
    widget.setStyleSheet(open(css_file, "r", encoding='utf-8').read())


# 設定主題
def set_theme(ui, system_settings):
    style = system_settings.field('外觀主題')
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
