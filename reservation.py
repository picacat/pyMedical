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
from libs import system_utils
from libs import registration_utils
from classes import table_widget
from dialog import dialog_reservation_booking


# 主視窗
class Reservation(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Reservation, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.reserve_key = args[2]
        self.ui = None
        self.max_reservation_table_times = 4
        self.max_reservation_table_rows = 20
        self.table_header = ['時間', '診號', '姓名', 'reserve_key']
        self.table_header_width = [70, 50, 100, 60]
        self.tab_name = '預約一覽表'

        self._set_ui()
        self._set_signal()
        self.read_reservation()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_RESERVATION, self)
        self.table_widget_reservation = table_widget.TableWidget(
            self.ui.tableWidget_reservation, self.database
        )
        self.table_widget_reservation_list = table_widget.TableWidget(
            self.ui.tableWidget_reservation_list, self.database
        )
        ui_utils.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM)
        self.ui.dateEdit_reservation_date.setDate(datetime.datetime.today())
        self.ui.dateEdit_start_date.setDate(datetime.datetime.today())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.today())

        self.table_widget_reservation_list.set_column_hidden([0])
        self.ui.tabWidget_reservation.setCurrentIndex(0)

        period = registration_utils.get_period(self.system_settings)
        self._set_radio_button_period(period)

        self.ui.action_cancel_reservation.setEnabled(False)
        self.ui.action_reservation_arrival.setEnabled(False)

    def _set_radio_button_period(self, period):
        if period == '早班':
            self.ui.radioButton_period1.setChecked(True)
        elif period == '午班':
            self.ui.radioButton_period2.setChecked(True)
        elif period == '晚班':
            self.ui.radioButton_period3.setChecked(True)

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_reservation)
        self.ui.action_save_table.triggered.connect(self._save_table)
        self.ui.action_cancel_reservation.triggered.connect(self._cancel_reservation)
        self.ui.action_reservation_arrival.triggered.connect(self.reservation_arrival)
        self.ui.dateEdit_reservation_date.dateChanged.connect(self.read_reservation)
        self.ui.radioButton_period1.clicked.connect(self.read_reservation)
        self.ui.radioButton_period2.clicked.connect(self.read_reservation)
        self.ui.radioButton_period3.clicked.connect(self.read_reservation)
        self.ui.comboBox_room.currentTextChanged.connect(self.read_reservation)
        self.ui.tableWidget_reservation.doubleClicked.connect(self._booking_reservation)
        self.ui.tabWidget_reservation.currentChanged.connect(self._tab_changed)                   # 切換分頁
        self.ui.dateEdit_start_date.dateChanged.connect(self._read_reservation_list)
        self.ui.dateEdit_end_date.dateChanged.connect(self._read_reservation_list)
        self.ui.radioButton_arrival1.clicked.connect(self._read_reservation_list)
        self.ui.radioButton_arrival2.clicked.connect(self._read_reservation_list)
        self.ui.radioButton_arrival3.clicked.connect(self._read_reservation_list)
        self.ui.tableWidget_reservation.itemSelectionChanged.connect(self._reservation_table_item_changed)

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

    def read_reservation(self):
        self._set_reservation_table()
        self._set_reservation_data()

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

    def _set_reservation_data(self):
        room = self.ui.comboBox_room.currentText()
        period = self._get_period()

        for row_no in range(self.ui.tableWidget_reservation.rowCount()):
            for i in range(1, self.max_reservation_table_times+1):
                col_no = (i-1) * len(self.table_header)
                time = self.ui.tableWidget_reservation.item(row_no, col_no)
                if time is None:
                    continue

                reserve_no = self.ui.tableWidget_reservation.item(row_no, col_no+1)
                reservation_date = '{0} {1}'.format(
                    self.ui.dateEdit_reservation_date.date().toString('yyyy-MM-dd'),
                    time.text()
                )
                sql = '''
                    SELECT * FROM reserve 
                    WHERE
                        ReserveDate = "{0}" AND
                        Period = "{1}" AND
                        Room = {2} AND
                        ReserveNo = {3}
                '''.format(
                    reservation_date, period, room, reserve_no.text()
                )
                rows = self.database.select_record(sql)
                if len(rows) <= 0:
                    continue

                self.ui.tableWidget_reservation.setItem(
                    row_no, col_no+2,
                    QtWidgets.QTableWidgetItem(string_utils.xstr(rows[0]['Name']))
                )
                self.ui.tableWidget_reservation.setItem(
                    row_no, col_no+3,
                    QtWidgets.QTableWidgetItem(string_utils.xstr(rows[0]['ReserveKey']))
                )

                if rows[0]['Arrival'] == 'True':
                    for i in range(3):
                        self.ui.tableWidget_reservation.item(
                            row_no, col_no+i).setForeground(
                            QtGui.QColor('gray')
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

        dialog.exec_()
        self.read_reservation()

        dialog.deleteLater()

    def _tab_changed(self, i):
        self.tab_name = self.ui.tabWidget_reservation.tabText(i)
        if self.tab_name == '預約一覽表':
            self.read_reservation()
        else:
            self._read_reservation_list()

    def _read_reservation_list(self):
        self.ui.tableWidget_reservation_list.setRowCount(1)

        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')

        arrival = ''
        if self.ui.radioButton_arrival1.isChecked():
            arrival = 'AND Arrival = "False"'
        elif self.ui.radioButton_arrival2.isChecked():
            arrival = 'AND Arrival = "True"'

        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveDate BETWEEN "{0}" AND "{1}"
                {2}
            ORDER BY ReserveDate, FIELD(Period, {3}), ReserveNo
        '''.format(
            start_date,
            end_date,
            arrival,
            str(nhi_utils.PERIOD)[1:-1]
        )

        self.table_widget_reservation_list.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row_data):
        if string_utils.xstr(row_data['Arrival']) == 'True':
            arrival = '已報到'
        else:
            arrival = '未報到'

        reservation_list_data = [
            string_utils.xstr(row_data['ReserveKey']),
            string_utils.xstr(row_data['ReserveDate']),
            string_utils.xstr(row_data['Period']),
            string_utils.xstr(row_data['PatientKey']),
            string_utils.xstr(row_data['Name']),
            string_utils.xstr(row_data['Room']),
            string_utils.xstr(row_data['ReserveNo']),
            arrival,
        ]

        for column in range(len(reservation_list_data)):
            self.ui.tableWidget_reservation_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(reservation_list_data[column])
            )
            if column in [3, 5, 6]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [2]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _cancel_reservation(self):
        if self.tab_name == '預約一覽表':
            self._cancel_reservation_by_table()
        else:
            self._cancel_reservation_by_list()

    def _get_reserve_key_by_table(self, row_no, col_no):
        header = self.ui.tableWidget_reservation.horizontalHeaderItem(col_no)
        if header is None:
            return None

        header = header.text()
        if header != '姓名':
            return None

        name = self.ui.tableWidget_reservation.item(row_no, col_no)
        if name is None:
            return None

        reserve_key = self.ui.tableWidget_reservation.item(row_no, col_no + 1)
        if reserve_key is None:
            return None

        arrival = self._check_reservation_arrival(reserve_key.text())
        if arrival:  # 已報到
            return None

        reserve_key = reserve_key.text()

        return reserve_key

    def _get_name_by_table(self, row_no, col_no):
        header = self.ui.tableWidget_reservation.horizontalHeaderItem(col_no)
        if header is None:
            return None

        header = header.text()
        if header != '姓名':
            return None

        name = self.ui.tableWidget_reservation.item(row_no, col_no)
        if name is None:
            return None

        return name.text()

    def _cancel_reservation_by_table(self):
        current_row = self.ui.tableWidget_reservation.currentRow()
        current_column = self.ui.tableWidget_reservation.currentColumn()

        reserve_key = self._get_reserve_key_by_table(current_row, current_column)
        if reserve_key is None:
            return

        name = self._get_name_by_table(current_row, current_column)
        if self._delete_reserve_record(reserve_key, name):
            self.read_reservation()

    def _cancel_reservation_by_list(self):
        reserve_key = self.table_widget_reservation_list.field_value(0)
        arrival = self._check_reservation_arrival(reserve_key)
        if arrival:  # 已報到
            return

        name = self.table_widget_reservation_list.field_value(4)
        if self._delete_reserve_record(reserve_key, name):
            self._read_reservation_list()

    def _delete_reserve_record(self, reserve_key, name):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('取消預約掛號')
        msg_box.setText(
            "<font size='4' color='red'><b>確定取消{0}的預約掛號?</b></font>".format(
                name)
        )
        msg_box.setInformativeText("注意！預約掛號取消後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        cancel_reservation = msg_box.exec_()
        if not cancel_reservation:
            return False

        self.database.exec_sql('DELETE FROM reserve WHERE ReserveKey = {0}'.format(reserve_key))

        return True

    def _reservation_table_item_changed(self):
        current_row = self.ui.tableWidget_reservation.currentRow()
        current_column = self.ui.tableWidget_reservation.currentColumn()

        reserve_key = self._get_reserve_key_by_table(current_row, current_column)
        if reserve_key is None:
            enabled = False
        else:
            enabled = True

        self.ui.action_cancel_reservation.setEnabled(enabled)
        self.ui.action_reservation_arrival.setEnabled(enabled)

    def reservation_arrival(self):
        current_column = self.ui.tableWidget_reservation.currentColumn()
        header = self.ui.tableWidget_reservation.horizontalHeaderItem(current_column).text()
        if header != '姓名':
            return

        current_row = self.ui.tableWidget_reservation.currentRow()
        name = self.ui.tableWidget_reservation.item(current_row, current_column)
        if name is None:
            return

        reserve_key = self.ui.tableWidget_reservation.item(current_row, current_column+1).text()

        arrival = self._check_reservation_arrival(reserve_key)
        if arrival:  # 已報到
            return

        name = name.text()
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('預約掛號報到')
        msg_box.setText(
            "<font size='4' color='blue'><b>{0}確定預約掛號報到?</b></font>".format(
                name)
        )
        msg_box.setInformativeText("注意！預約掛號報到後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        arrival = msg_box.exec_()
        if not arrival:
            return

        self.parent.registration_arrival(reserve_key)

    def _check_reservation_arrival(self, reserve_key):
        arrival = False

        sql = '''
            SELECT * FROM reserve 
            WHERE
                ReserveKey = {0}
        '''.format(reserve_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return arrival

        if rows[0]['Arrival'] == 'True':
            arrival = True
            system_utils.show_message_box(
                QtWidgets.QMessageBox.Information,
                '已預約報到過了',
                '<font size="4" color="red"><b>此病患已預約報到過, 請重新選擇.</b></font>',
                '無效的動作.'
            )

        return arrival

    def set_reservation_arrival(self, reserve_key=None):
        # if reserve_key is None:
        #     reserve_key = self.reserve_key

        sql = '''
            SELECT * FROM reserve 
            WHERE
                ReserveKey = {0}
        '''.format(reserve_key)
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return

        row = rows[0]
        period = string_utils.xstr(row['Period'])
        self._set_radio_button_period(period)
        self.ui.comboBox_room.setCurrentText(string_utils.xstr(row['Room']))
        self.read_reservation()

        current_row, current_col = 0, 0
        for row_no in range(self.ui.tableWidget_reservation.rowCount()):
            for col_no in range(self.ui.tableWidget_reservation.columnCount()):
                reservation_key = self.ui.tableWidget_reservation.item(row_no, col_no)
                if reservation_key is not None and reservation_key.text() == string_utils.xstr(reserve_key):
                    current_row = row_no
                    current_col = col_no - 1
                    break

        self.ui.tableWidget_reservation.setCurrentCell(current_row, current_col)
