#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
import datetime
import re

from libs import ui_utils
from libs import system_utils
from libs import date_utils


# 病歷查詢視窗
class DialogStatisticsReturnRate(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogStatisticsReturnRate, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_STATISTICS_RETURN_RATE, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.dateEdit_start_date.setDate(datetime.datetime.now())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.now())
        self._set_combo_box()
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self._set_date_edit()

    def _set_date_edit(self):
        start_date = datetime.datetime.today().replace(day=1)
        self.ui.dateEdit_start_date.setDate(start_date)
        self.ui.dateEdit_end_date.setDate(datetime.datetime.today())

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    # 設定comboBox
    def _set_combo_box(self):
        script = 'select * from person where Position IN("醫師", "支援醫師")'
        rows = self.database.select_record(script)
        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        script = 'select * from person where Position IN("推拿師父")'
        rows = self.database.select_record(script)
        massager_list = []
        for row in rows:
            massager_list.append(row['Name'])

        return_days_list = ['7', '14', '21', '28', '30']
        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_doctor_return_days, return_days_list)

        ui_utils.set_combo_box(self.ui.comboBox_massager, massager_list, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_massager_return_days, return_days_list)

    def start_date(self):
        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')

        return start_date

    def end_date(self):
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')

        return end_date

    def doctor(self):
        doctor = self.ui.comboBox_doctor.currentText()

        return doctor

    def ins_type(self):
        ins_type = '全部'

        if self.ui.radioButton_ins.isChecked():
            ins_type = '健保'
        elif self.ui.radioButton_self.isChecked():
            ins_type = '自費'

        return ins_type

    def treat_type(self):
        treat_type = '全部'

        if self.ui.radioButton_general.isChecked():
            treat_type = '內科'
        elif self.ui.radioButton_acupuncture.isChecked():
            treat_type = '針灸治療'
        elif self.ui.radioButton_c_acupuncture.isChecked():
            treat_type = '複雜針灸'
        elif self.ui.radioButton_massage.isChecked():
            treat_type = '傷科治療'
        elif self.ui.radioButton_c_massage.isChecked():
            treat_type = '複雜傷科'

        return treat_type

    def visit(self):
        visit_type = '全部'

        if self.ui.radioButton_visited.isChecked():
            visit_type = '複診'
        elif self.ui.radioButton_first_visit.isChecked():
            visit_type = '初診'

        return visit_type

    def accepted_button_clicked(self):
        pass

