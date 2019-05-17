#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

import re
import datetime

from libs import system_utils
from libs import ui_utils
from libs import nhi_utils
from libs import patient_utils
from libs import string_utils
from libs import date_utils
from libs import number_utils
from libs import registration_utils


# 主視窗
class DialogReservationModify(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogReservationModify, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.reserve_key = args[2]

        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_data()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_RESERVATION_MODIFY, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self._set_combo_box()

    def _set_combo_box(self):
        sql = '''
            SELECT * FROM person 
            WHERE 
                Position IN ("醫師", "支援醫師")
        '''
        rows = self.database.select_record(sql)
        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD)
        ui_utils.set_combo_box(self.ui.comboBox_arrival, ['是', '否'])

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            return

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def accepted_button_clicked(self):
        reserve_date = '{reserve_date} {hour:0>2}:{minute:0>2}:00'.format(
            reserve_date=self.ui.dateEdit_reserve_date.date().toString('yyyy-MM-dd'),
            hour=self.ui.spinBox_hour.value(),
            minute=self.ui.spinBox_minute.value(),
        )
        period = self.ui.comboBox_period.currentText()
        reserve_no = self.ui.spinBox_reserve_no.value()
        doctor = self.ui.comboBox_doctor.currentText()

        if self.ui.comboBox_arrival.currentText() == '是':
            arrival = 'True'
        else:
            arrival = 'False'

        fields = [
            'ReserveDate', 'Period', 'ReserveNo',
            'Doctor', 'Arrival'
        ]

        data = [
            reserve_date,
            period,
            reserve_no,
            doctor,
            arrival,
        ]

        self.database.update_record('reserve', fields, 'ReserveKey', self.reserve_key, data)

    def _read_data(self):
        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveKey = {reserve_key}
        '''.format(
            reserve_key=self.reserve_key,
        )
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        self._set_reservation_data(row)

    def _set_reservation_data(self, row):
        patient_key = string_utils.xstr(row['PatientKey'])
        if string_utils.xstr(row['Source']) == '網路初診預約':
            patient_key = '網路初診'

        try:
            hour = row['ReserveDate'].hour
            minute = row['ReserveDate'].minute
        except:
            hour = 0
            minute = 0

        self.ui.lineEdit_patient_key.setText(patient_key)
        self.ui.lineEdit_name.setText(string_utils.xstr(row['Name']))
        self.ui.dateEdit_reserve_date.setDate(row['ReserveDate'].date())
        self.ui.spinBox_hour.setValue(hour)
        self.ui.spinBox_minute.setValue(minute)
        self.ui.spinBox_reserve_no.setValue(number_utils.get_integer(row['ReserveNo']))
        self.ui.comboBox_period.setCurrentText(string_utils.xstr(row['Period']))
        self.ui.comboBox_doctor.setCurrentText(string_utils.xstr(row['Doctor']))

        if string_utils.xstr(row['Arrival']) == 'True':
            arrival = '是'
        else:
            arrival = '否'

        self.ui.comboBox_arrival.setCurrentText(arrival)

