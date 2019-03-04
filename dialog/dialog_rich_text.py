#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore

from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils


# 主視窗
class DialogRichText(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogRichText, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.text_format = args[2]  # rich_text, plain_text, html
        self.text = args[3]

        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_RICH_TEXT, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self._set_text()

    def _set_text(self):
        if self.text_format == 'rich_text':
            self.ui.textEdit_rich_text.setText(self.text)
        elif self.text_format == 'plain_text':
            self.ui.textEdit_rich_text.setPlainText(self.text)
        elif self.text_format == 'html':
            self.ui.textEdit_rich_text.setHtml(self.text)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def accepted_button_clicked(self):
        self.close()

