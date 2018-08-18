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
class DialogNurseSchedule(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogNurseSchedule, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.schedule_date = args[2]
        self.doctor = args[3]
        self.nurse1 = args[4]
        self.nurse2 = args[5]
        self.nurse3 = args[6]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_NURSE_SCHEDULE, self)
        system_utils.set_css(self)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.lineEdit_schedule_date.setText(self.schedule_date)
        self.ui.lineEdit_doctor.setText(self.doctor)
        self._set_combo_box()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def _set_combo_box(self):
        script = 'select * from person where Position = "護士"'
        rows = self.database.select_record(script)
        nurse_list = []
        for row in rows:
            nurse_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_nurse1, nurse_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_nurse2, nurse_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_nurse3, nurse_list, None)
        self.ui.comboBox_nurse1.setCurrentText(self.nurse1)
        self.ui.comboBox_nurse2.setCurrentText(self.nurse2)
        self.ui.comboBox_nurse3.setCurrentText(self.nurse3)

    def accepted_button_clicked(self):
        pass
