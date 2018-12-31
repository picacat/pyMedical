#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

import re
import datetime

from libs import system_utils
from libs import ui_utils
from libs import validator_utils
from libs import patient_utils
from libs import string_utils
from libs import date_utils


# 主視窗
class DialogReservationBooking(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogReservationBooking, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.reservation_date = args[2]
        self.period = args[3]
        self.room = args[4]
        self.reserve_no = args[5]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_RESERVATION_BOOKING, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.lineEdit_reservation_date.setText(self.reservation_date)
        self.ui.lineEdit_period.setText(self.period)
        self.ui.lineEdit_room.setText(self.room)
        self.ui.lineEdit_reserve_no.setText(self.reserve_no)
        ui_utils.set_completer(
            self.database,
            'SELECT Name FROM patient GROUP BY Name ORDER BY Name',
            'Name',
            self.ui.lineEdit_query
        )

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            return

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.pushButton_query.clicked.connect(self._query_patient)
        self.ui.lineEdit_query.returnPressed.connect(self._query_patient)

    def accepted_button_clicked(self):
        fields = [
            'PatientKey', 'Name', 'ReserveDate', 'Period',
            'Room', 'ReserveNo'
        ]

        data = [
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            self.ui.lineEdit_reservation_date.text(),
            self.ui.lineEdit_period.text(),
            self.ui.lineEdit_room.text(),
            self.ui.lineEdit_reserve_no.text(),
        ]
        self.database.insert_record('reserve', fields, data)

    # 開始查詢病患資料
    def _query_patient(self):
        keyword = string_utils.xstr(self.ui.lineEdit_query.text())
        if keyword == '':
            return

        pattern = re.compile(validator_utils.DATE_REGEXP)
        if pattern.match(keyword):
            keyword = date_utils.date_to_west_date(keyword)

        self._get_patient(keyword)

    def _get_patient(self, keyword, ic_card=None):
        row = patient_utils.search_patient(self.ui, self.database, self.system_settings, keyword)
        if row is None: # 找不到資料
            system_utils.show_message_box(
                QMessageBox.Critical,
                '查無資料',
                '<font size="4" color="red"><b>找不到有關的病患資料, 請檢查關鍵字是否有誤.</b></font>',
                '請確定輸入資料的正確性, 生日請輸入YYYY-MM-DD.'
            )
            self.ui.lineEdit_query.setFocus()
        elif row == -1:  # 取消查詢
            self.ui.lineEdit_query.setFocus()
        else:  # 已選取病患
            self._set_patient_data(row)

        self.ui.lineEdit_query.clear()

    def _set_patient_data(self, rows):
        row = rows[0]
        patient_key = row['PatientKey']

        self.ui.lineEdit_patient_key.setText(string_utils.xstr(patient_key))
        self.ui.lineEdit_name.setText(string_utils.xstr(row['Name']))
        self.ui.lineEdit_birthday.setText(string_utils.xstr(row['Birthday']))
        self.ui.lineEdit_id.setText(string_utils.xstr(row['ID']))

        start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')
        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveDate BETWEEN "{0}" AND "{1}" AND
                PatientKey = {2}
        '''.format(
            start_date, end_date, patient_key
        )

        rows = self.database.select_record(sql)
        if len(rows) > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('已有預約')
            msg_box.setText("此人今日已有預約, 無法再次預約掛號.")
            msg_box.setInformativeText("無法重複預約掛號.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            self.ui.lineEdit_patient_key.setText(None)
            self.ui.lineEdit_name.setText(None)
            self.ui.lineEdit_birthday.setText(None)
            self.ui.lineEdit_id.setText(None)
            return

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
