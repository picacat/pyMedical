#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
import datetime
import calendar

from libs import system_utils
from libs import ui_utils
from libs import number_utils


# 主視窗
class DialogDatePicker(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogDatePicker, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_DATE_PICKER, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self._set_combo_box()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def _set_combo_box(self):
        year_list = []
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        for i in range(current_year, current_year - 10, -1):
            year_list.append(str(i))

        ui_utils.set_combo_box(self.ui.comboBox_year, year_list)
        self.ui.comboBox_year.setCurrentText(str(current_year))
        self.ui.comboBox_month.setCurrentText(str(current_month))

    def accepted_button_clicked(self):
        pass

