#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from classes import table_widget


# 主視窗
class DialogReservationQuery(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogReservationQuery, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_RESERVATION_QUERY, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('關閉')
        self.table_widget_reservation = table_widget.TableWidget(self.ui.tableWidget_reservation, self.database)
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.lineEdit_keyword.textChanged.connect(self._query_reservation)
        self.ui.radioButton_unarrival.clicked.connect(self._query_reservation)
        self.ui.radioButton_arrival.clicked.connect(self._query_reservation)
        self.ui.radioButton_all.clicked.connect(self._query_reservation)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 90, 120, 50, 50, 90, 120, 120]
        self.table_widget_reservation.set_table_heading_width(width)

    def _query_reservation(self):
        keyword = self.ui.lineEdit_keyword.text()
        if keyword == '':
            self.ui.tableWidget_reservation.setRowCount(0)
            return

        if self.ui.radioButton_unarrival.isChecked():
            condition = ' AND Arrival = "False" '
        elif self.ui.radioButton_arrival.isChecked():
            condition = ' AND Arrival = "True" '
        else:
            condition = ''

        if keyword.isdigit():
            patient_condition = 'PatientKey = {0}'.format(keyword)
        else:
            patient_condition = 'Name LIKE "%{0}%"'.format(keyword)

        sql = '''
            SELECT * FROM reserve 
            WHERE
                {patient_condition}
                {condition}
            ORDER BY PatientKey, ReserveDate DESC
        '''.format(
            patient_condition=patient_condition,
            condition=condition,
        )
        self.table_widget_reservation.set_db_data(sql, self._set_reservation_data)

        self.ui.lineEdit_keyword.setFocus(True)
        self.ui.lineEdit_keyword.setCursorPosition(len(keyword))

    def _set_reservation_data(self, row_no, row):
        if string_utils.xstr(row['Arrival']) == 'True':
            status = '已報到'
        else:
            status = '未報到'

        if row['ReserveDate'] is None:
            reserve_date = None
        else:
            reserve_date = string_utils.xstr(row['ReserveDate'].date())

        reservation_data = [
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            reserve_date,
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['ReserveNo']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['Source']),
            status,
        ]

        for col_no in range(len(reservation_data)):
            self.ui.tableWidget_reservation.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(reservation_data[col_no])
            )

            if col_no in [0, 4]:
                self.ui.tableWidget_reservation.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [3]:
                self.ui.tableWidget_reservation.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )


