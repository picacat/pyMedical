# 元件設定 2017.09.26

#coding: utf-8
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton
import sys
import os
import subprocess
import socket

if sys.platform == 'win32':
    from win32con import WM_INPUTLANGCHANGEREQUEST
    import win32api
    import win32gui

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname("__file__")))
CSS_PATH = "css"


def center_window(window):
    frame_geometry = window.frameGeometry()
    center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
    frame_geometry.moveCenter(center_point)
    window.move(frame_geometry.topLeft())


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()

    return IP


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
        font = 'Monospace'

    return font


def set_login_image(widget, system_settings):
    image_file = 'login_blue.jpg'

    if system_settings.field('外觀顏色') == '紅色':
        image_file = 'login_red.jpg'
    elif system_settings.field('外觀顏色') == '綠色':
        image_file = 'login_green.jpg'
    elif system_settings.field('外觀顏色') == '藍色':
        image_file = 'login_blue.jpg'
    elif system_settings.field('外觀顏色') == '灰色':
        image_file = 'login_gray.jpg'

    style = '''
        QDialog#Dialog_login
        {{background-image: url(images/{image_file});}}
    '''.format(
        image_file=image_file,
    )
    widget.setStyleSheet(style)


def set_background_image(widget, system_settings):
    image_file = 'home_blue.jpg'

    if system_settings.field('外觀顏色') == '紅色':
        image_file = 'home_red.jpg'
    elif system_settings.field('外觀顏色') == '綠色':
        image_file = 'home_green.jpg'
    elif system_settings.field('外觀顏色') == '藍色':
        image_file = 'home_blue.jpg'
    elif system_settings.field('外觀顏色') == '灰色':
        image_file = 'home_gray.jpg'

    style = '''
        QWidget#tab_home
        {{background-image: url(./images/{image_file});}}
    '''.format(
        image_file=image_file,
    )
    widget.setStyleSheet(style)


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


def set_keyboard_layout(lang):
    if sys.platform != 'win32':
        return

    chinese = 0x0404
    english = 0x0409

    if lang == '中文':
        keyboard = chinese
    else:
        keyboard = english

    hwnd = win32gui.GetForegroundWindow()

    win32api.SendMessage(
        hwnd,
        WM_INPUTLANGCHANGEREQUEST,
        0,
        keyboard
    )


def unzip_file(zip_file, output_directory):
    cmd = ['7z', 'x', zip_file, '-o{output_directory}'.format(output_directory=output_directory)]
    sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    sp.communicate()


def get_host_ip():
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def set_widget_image(widget, image_file):
    style_sheet = '''
        QWidget {{
            background-image: url({image_file});
            background-repeat: none;
            background-position: center;
        }}
        QPushButton {{
            color: rgb(255, 0, 0);
            font: 10pt;
        }}
    '''.format(
        image_file=image_file,
    )

    widget.setStyleSheet(style_sheet)


def set_combo_box_item(combo_box, item_text):
    item_exists = False
    for i in range(combo_box.count()):
        if combo_box.itemText(i) == item_text:
            item_exists = True
            break

    if not item_exists:
        combo_box.insertItem(1, item_text)

    combo_box.setCurrentText(item_text)
