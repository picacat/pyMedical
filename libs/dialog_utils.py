
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QPushButton


def get_font():
    font = QFont()
    font.setPixelSize(16)

    return font


def get_dialog(title, label, text_value, input_mode, height, width):
    font = get_font()
    input_dialog = QInputDialog()
    input_dialog.setFont(font)
    input_dialog.setInputMode(input_mode)
    input_dialog.resize(height, width)
    input_dialog.setWindowTitle(title)
    input_dialog.setLabelText(label)
    input_dialog.setTextValue(text_value)
    input_dialog.setOkButtonText('確定')
    input_dialog.setCancelButtonText('取消')

    return input_dialog


def get_message_box(title, icon, text, info_text):
    font = get_font()
    msg_box = QMessageBox()
    msg_box.setFont(font)
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setInformativeText(info_text)
    msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
    msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)

    return msg_box


def message_box(title, message, hint):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setInformativeText(hint)
    msg_box.setStandardButtons(QMessageBox.NoButton)

    return msg_box


def message_box_with_button(title, message, hint):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setInformativeText(hint)
    msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)

    return msg_box


