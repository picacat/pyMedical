#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime

from libs import ui_utils
from libs import nhi_utils
from libs import string_utils
from libs import number_utils
from classes import table_widget
from dialog import dialog_reservation_booking


# 主視窗
class Reservation(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Reservation, self).__init__(parent)
        self.parent = parent
        self.database = args[0][0]
        self.system_settings = args[0][1]
        self.patientKey = args[0][2]
        self.ui = None
        self.max_reservation_table_times = 4
        self.max_reservation_table_rows = 20
        self.table_header = ['時間', '診號', '姓名', 'reserve_key']
        self.table_header_width = [70, 50, 100, 60]

        self._set_ui()
        self._set_signal()
        self._read_reservation()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_RESERVATION, self)
        self.table_widget_reservation = table_widget.TableWidget(self.ui.tableWidget_reservation, self.database)
        ui_utils.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM)
        self.ui.dateEdit_reservation_date.setDate(datetime.datetime.today())

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_reservation)
        self.ui.action_save_table.triggered.connect(self._save_table)
        self.ui.radioButton_period1.clicked.connect(self._read_reservation)
        self.ui.radioButton_period2.clicked.connect(self._read_reservation)
        self.ui.radioButton_period3.clicked.connect(self._read_reservation)
        self.ui.comboBox_room.currentTextChanged.connect(self._read_reservation)
        self.ui.tableWidget_reservation.doubleClicked.connect(self._booking_reservation)

    # 設定欄位寬度
    def _set_table_width(self):
        width = self.table_header_width * self.max_reservation_table_times
        self.table_widget_reservation.set_table_heading_width(width)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_reservation(self):
        self.close_all()
        self.close_tab()

    def _read_reservation(self):
        self._set_reservation_table()

    def _set_reservation_table(self):
        self.ui.tableWidget_reservation.clear()

        max_reservation_table_columns = len(self.table_header) * self.max_reservation_table_times
        self.ui.tableWidget_reservation.setColumnCount(max_reservation_table_columns)
        self.ui.tableWidget_reservation.setRowCount(self.max_reservation_table_rows)
        self.ui.tableWidget_reservation.setHorizontalHeaderLabels(
            self.table_header * self.max_reservation_table_times
        )
        self._set_table_width()

        hidden_columns = [i * len(self.table_header) - 1 for i in range(1, self.max_reservation_table_times+1)]
        self.table_widget_reservation.set_column_hidden(hidden_columns)

        room = self.ui.comboBox_room.currentText()
        period = self._get_period()

        sql = '''
            SELECT * FROM reservation_table
            WHERE
                Room = "{0}" AND
                Period = "{1}"
            ORDER BY RowNo, ColumnNo
        '''.format(room, period)
        rows = self.database.select_record(sql)

        for row in rows:
            self.ui.tableWidget_reservation.setItem(
                number_utils.get_integer(row['RowNo']),
                number_utils.get_integer(row['ColumnNo']),
                QtWidgets.QTableWidgetItem(string_utils.xstr(row['Time']))
            )
            self.ui.tableWidget_reservation.setItem(
                number_utils.get_integer(row['RowNo']),
                number_utils.get_integer(row['ColumnNo']+1),
                QtWidgets.QTableWidgetItem(string_utils.xstr(row['ReserveNo']))
            )
            self.ui.tableWidget_reservation.item(
                number_utils.get_integer(row['RowNo']),
                number_utils.get_integer(row['ColumnNo'])).setTextAlignment(
                QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
            )
            self.ui.tableWidget_reservation.item(
                number_utils.get_integer(row['RowNo']),
                number_utils.get_integer(row['ColumnNo']+1)).setTextAlignment(
                QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
            )

    def _save_table(self):
        room = self.ui.comboBox_room.currentText()
        period = self._get_period()

        sql = '''
            DELETE FROM reservation_table
            WHERE
                Room = "{0}" AND Period = "{1}"
        '''.format(
            room, period
        )
        self.database.exec_sql(sql)

        for row_no in range(self.ui.tableWidget_reservation.rowCount()):
            for i in range(1, self.max_reservation_table_times+1):
                col_no = (i-1) * len(self.table_header)
                time = self.ui.tableWidget_reservation.item(row_no, col_no)
                reserve_no = self.ui.tableWidget_reservation.item(row_no, col_no+1)
                if time != None and reserve_no != None:
                    self._insert_reservation_table(
                        period, room, row_no, col_no,
                        time.text(), reserve_no.text()
                    )

    def _insert_reservation_table(self, period, room, row_no, col_no, time, reserve_no):
        fields = [
            'Period', 'Room', 'RowNo', 'ColumnNo', 'Time', 'ReserveNo'
        ]

        data = [
            period, room, row_no, col_no, time, reserve_no
        ]

        self.database.insert_record('reservation_table', fields, data)

    def _get_period(self):
        period = None
        if self.ui.radioButton_period1.isChecked():
            period = '早班'
        elif self.ui.radioButton_period2.isChecked():
            period = '午班'
        elif self.ui.radioButton_period3.isChecked():
            period = '晚班'

        return period

    def _booking_reservation(self):
        current_column = self.ui.tableWidget_reservation.currentColumn()
        header = self.ui.tableWidget_reservation.horizontalHeaderItem(current_column).text()
        if header != '姓名':
            return

        current_row = self.ui.tableWidget_reservation.currentRow()
        name = self.ui.tableWidget_reservation.item(current_row, current_column)
        if name is not None:  # 已被預約
            return

        time = self.ui.tableWidget_reservation.item(current_row, current_column-2)
        reserve_no = self.ui.tableWidget_reservation.item(current_row, current_column-1)
        if time is None or reserve_no is None:
            return

        time = time.text()
        reserve_no = reserve_no.text()
        room = self.ui.comboBox_room.currentText()
        period = self._get_period()
        reservation_date = '{0} {1}'.format(
            self.ui.dateEdit_reservation_date.date().toString('yyyy-MM-dd'),
            time
        )

        dialog = dialog_reservation_booking.DialogReservationBooking(
            self, self.database, self.system_settings,
            reservation_date, period, room, reserve_no,
        )

        dialog.exec()
        self._read_reservation()

        dialog.deleteLater()
