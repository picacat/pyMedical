#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
import datetime

from libs import system_utils
from libs import ui_utils
from libs import nhi_utils
from libs import personnel_utils
from libs import string_utils


# 主視窗
class DialogIncome(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogIncome, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INCOME, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')

        script = 'select * from person where Position IN("醫師", "支援醫師") '
        rows = self.database.select_record(script)
        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list, '全部')
        ui_utils.set_combo_box(
            self.ui.comboBox_cashier,
            personnel_utils.get_personnel(self.database, '全部'), '全部',
        )
        self.ui.dateEdit_case_date.setDate(datetime.datetime.today())

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.button_accepted)
        self.ui.buttonBox.rejected.connect(self.button_rejected)

    def button_accepted(self):
        self.start_date = self.ui.dateEdit_case_date.date().toString('yyyy-MM-dd 00:00:00')
        self.end_date = self.ui.dateEdit_case_date.date().toString('yyyy-MM-dd 23:59:59')

        self.period = '全部'
        if self.ui.radioButton_period1.isChecked():
            self.period = '早班'
        elif self.ui.radioButton_period2.isChecked():
            self.period = '午班'
        elif self.ui.radioButton_period3.isChecked():
            self.period = '晚班'

        self.doctor = self.ui.comboBox_doctor.currentText()
        self.cashier = self.ui.comboBox_cashier.currentText()

    def button_rejected(self):
        pass
