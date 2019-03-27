#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime

from libs import ui_utils
from libs import date_utils
from libs import nhi_utils
from libs import string_utils
from libs import number_utils
from libs import patient_utils
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

        self.ui.dateEdit_reservation_date.setDate(datetime.datetime.today())
        self._set_week_day()

        self.ui.dateEdit_start_date.setDate(datetime.datetime.today())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.today())

        self.table_widget_reservation_list.set_column_hidden([0])
        self.ui.tabWidget_reservation.setCurrentIndex(0)

        period = registration_utils.get_period(self.system_settings)
        self._set_radio_button_period(period)

        self.ui.action_add_reservation.setEnabled(False)
        self.ui.action_cancel_reservation.setEnabled(False)
        self.ui.action_reservation_arrival.setEnabled(False)
        ui_utils.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM)

        self._set_combo_box_doctor()

    def _set_week_day(self):
        current_week_day = datetime.datetime(
            self.ui.dateEdit_reservation_date.date().year(),
            self.ui.dateEdit_reservation_date.date().month(),
            self.ui.dateEdit_reservation_date.date().day(),
        ).weekday()

        week_day_name = date_utils.get_weekday_name(current_week_day)
        self.ui.label_weekday_name.setText(week_day_name)

    # 設定醫師
    def _set_combo_box_doctor(self):
        script = '''
            SELECT * FROM person 
            WHERE 
                Position IN ("醫師", "支援醫師")
        '''
        rows = self.database.select_record(script)

        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list)

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

        self.ui.tableWidget_reservation.doubleClicked.connect(self._booking_reservation)
        self.ui.action_add_reservation.triggered.connect(self._booking_reservation)

        self.ui.tabWidget_reservation.currentChanged.connect(self._tab_changed)                   # 切換分頁
        self.ui.dateEdit_start_date.dateChanged.connect(self._read_reservation_list)
        self.ui.dateEdit_end_date.dateChanged.connect(self._read_reservation_list)
        self.ui.radioButton_arrival1.clicked.connect(self._read_reservation_list)
        self.ui.radioButton_arrival2.clicked.connect(self._read_reservation_list)
        self.ui.radioButton_arrival3.clicked.connect(self._read_reservation_list)
        self.ui.tableWidget_reservation.itemSelectionChanged.connect(self._reservation_table_item_changed)
        self.ui.tableWidget_reservation_list.itemSelectionChanged.connect(self._reservation_list_changed)

        self.ui.comboBox_doctor.currentTextChanged.connect(self.read_reservation)
        self.ui.comboBox_room.currentTextChanged.connect(self.read_reservation)

        self.ui.dateEdit_reservation_date.dateChanged.connect(self._set_week_day)

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
        doctor = self.ui.comboBox_doctor.currentText()
        period = self._get_period()

        sql = '''
            SELECT * FROM reservation_table
            WHERE
                (Room="{room}") AND
                (Doctor="{doctor}") AND
                (Period = "{period}")
            ORDER BY RowNo, ColumnNo
        '''.format(
            room=room,
            doctor=doctor,
            period=period,
        )
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
        doctor = self.ui.comboBox_doctor.currentText()
        period = self._get_period()

        for row_no in range(self.ui.tableWidget_reservation.rowCount()):
            for i in range(1, self.max_reservation_table_times+1):
                col_no = (i-1) * len(self.table_header)
                time = self.ui.tableWidget_reservation.item(row_no, col_no)
                if time is None:
                    continue

                reserve_no = self.ui.tableWidget_reservation.item(row_no, col_no+1)
                if reserve_no.text() == '':
                    continue

                reservation_date = '{0} {1}'.format(
                    self.ui.dateEdit_reservation_date.date().toString('yyyy-MM-dd'),
                    time.text()
                )
                sql = '''
                    SELECT * FROM reserve 
                    WHERE
                        ReserveDate = "{reservation_date}" AND
                        Period = "{period}" AND
                        room = "{room}" AND
                        Doctor = "{doctor}" AND
                        ReserveNo = {reserve_no}
                '''.format(
                    reservation_date=reservation_date,
                    period=period,
                    room=room,
                    doctor=doctor,
                    reserve_no=reserve_no.text(),
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
                    color = 'gray'
                elif string_utils.xstr(rows[0]['Source']) == '網路預約':
                    color = 'blue'
                elif string_utils.xstr(rows[0]['Source']) == '網路初診預約':
                    color = 'green'
                else:
                    color = 'black'

                for i in range(3):
                    self.ui.tableWidget_reservation.item(
                        row_no, col_no+i).setForeground(
                        QtGui.QColor(color)
                    )

    def _save_table(self):
        room = self.ui.comboBox_room.currentText()
        doctor = self.ui.comboBox_doctor.currentText()
        period = self._get_period()

        sql = '''
            DELETE FROM reservation_table
            WHERE
                Room = "{room}" AND
                Doctor = "{doctor}" AND 
                Period = "{period}"
        '''.format(
            room=room,
            doctor=doctor,
            period=period,
        )
        self.database.exec_sql(sql)

        for row_no in range(self.ui.tableWidget_reservation.rowCount()):
            for i in range(1, self.max_reservation_table_times+1):
                col_no = (i-1) * len(self.table_header)
                time = self.ui.tableWidget_reservation.item(row_no, col_no)
                reserve_no = self.ui.tableWidget_reservation.item(row_no, col_no+1)
                if time != None and reserve_no != None:
                    self._insert_reservation_table(
                        room, period, doctor, row_no, col_no,
                        time.text(), reserve_no.text()
                    )

    def _insert_reservation_table(self, room, period, doctor, row_no, col_no, time, reserve_no):
        fields = [
            'Room', 'Period', 'Doctor', 'RowNo', 'ColumnNo', 'Time', 'ReserveNo'
        ]

        data = [
            room, period, doctor, row_no, col_no, time, reserve_no
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
        current_row = self.ui.tableWidget_reservation.currentRow()

        header = self.ui.tableWidget_reservation.horizontalHeaderItem(current_column).text()
        if header != '姓名':
            return

        name = self.ui.tableWidget_reservation.item(current_row, current_column)
        if name is not None:  # 已被預約, 呼叫報到程序
            self.reservation_arrival()
            return

        time = self.ui.tableWidget_reservation.item(current_row, current_column-2)
        reserve_no = self.ui.tableWidget_reservation.item(current_row, current_column-1)
        if time is not None:
            time = time.text()
        else:
            time = ''

        if reserve_no is not None:
            reserve_no = reserve_no.text()
        else:
            reserve_no = ''

        if time == '' and reserve_no == '':
            return

        doctor = self.ui.comboBox_doctor.currentText()
        period = self._get_period()
        room = self.ui.comboBox_room.currentText()
        reservation_date = '{0} {1}'.format(
            self.ui.dateEdit_reservation_date.date().toString('yyyy-MM-dd'),
            time
        )

        dialog = dialog_reservation_booking.DialogReservationBooking(
            self, self.database, self.system_settings,
            reservation_date, period, doctor, room, reserve_no,
        )

        dialog.exec_()
        self.read_reservation()

        dialog.deleteLater()

    def _tab_changed(self, i):
        self.tab_name = self.ui.tabWidget_reservation.tabText(i)

        if self.tab_name == '預約一覽表':
            self.ui.action_save_table.setEnabled(True)
            self.read_reservation()
            enabled = False
            self.ui.tableWidget_reservation.setCurrentCell(0, 0)
            self.ui.tableWidget_reservation.setFocus()
        else:
            self.ui.action_add_reservation.setEnabled(False)
            self.ui.action_save_table.setEnabled(False)

            self._read_reservation_list()

            if self.table_widget_reservation_list.row_count() > 0:
                enabled = True
            else:
                enabled = False

        self.ui.action_reservation_arrival.setEnabled(enabled)
        self.ui.action_cancel_reservation.setEnabled(enabled)


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
            string_utils.xstr(row_data['Doctor']),
            string_utils.xstr(row_data['Room']),
            string_utils.xstr(row_data['ReserveNo']),
            arrival,
            string_utils.xstr(row_data['Source']),
        ]

        for column in range(len(reservation_list_data)):
            self.ui.tableWidget_reservation_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(reservation_list_data[column])
            )
            if column in [3, 6, 7]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [2]:
                self.ui.tableWidget_reservation_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

        if string_utils.xstr(row_data['Source']) == '網路預約':
            color = 'blue'
        elif string_utils.xstr(row_data['Source']) == '網路初診預約':
            color = 'green'
        else:
            color = 'black'

        for col_no in range(self.ui.tableWidget_reservation_list.columnCount()):
            self.ui.tableWidget_reservation_list.item(
                row_no, col_no).setForeground(
                QtGui.QColor(color)
            )

    def _cancel_reservation(self):
        if self.tab_name == '預約一覽表':
            self._cancel_reservation_by_table()
        else:
            self._cancel_reservation_by_list()

    def _get_reserve_key_by_table(self, row_no, col_no, warning=False):
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

        reserve_key = self._get_reserve_key_by_table(current_row, current_column, True)
        if reserve_key is None:
            return

        name = self._get_name_by_table(current_row, current_column)
        if self._delete_reserve_record(reserve_key, name):
            self.read_reservation()

    def _cancel_reservation_by_list(self):
        reserve_key = self.table_widget_reservation_list.field_value(0)
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

        self._set_action_add_reservation()

    def _set_action_add_reservation(self):
        current_row = self.ui.tableWidget_reservation.currentRow()
        current_column = self.ui.tableWidget_reservation.currentColumn()

        self.ui.action_add_reservation.setEnabled(False)
        header = self.ui.tableWidget_reservation.horizontalHeaderItem(current_column).text()
        if header == '姓名':
            time = self.ui.tableWidget_reservation.item(current_row, current_column-2)
            reservation_no = self.ui.tableWidget_reservation.item(current_row, current_column-1)
            name = self.ui.tableWidget_reservation.item(current_row, current_column)

            if time is not None:
                time = time.text()
            else:
                time = ''

            if reservation_no is not None:
                reservation_no = reservation_no.text()
            else:
                reservation_no = ''

            if name is not None:
                name = name.text()
            else:
                name = ''

            if time != '' and reservation_no != '' and name == '':
                self.ui.action_add_reservation.setEnabled(True)

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

        reserve_row = self._check_reservation_first_visit(reserve_key)  # 檢查是否為初診預約報到
        if reserve_row is not None:
            self._first_visit_arrival(reserve_row)
            return

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

    def _check_reservation_first_visit(self, reserve_key):
        first_visit = None

        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveKey = {reserve_key}
        '''.format(
            reserve_key=reserve_key,
        )
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return first_visit

        row = rows[0]

        reservation_source = string_utils.xstr(row['Source'])
        if reservation_source != '網路初診預約':
            return first_visit

        return row

    def _first_visit_arrival(self, reserve_row):
        sql = '''
            SELECT * FROM temp_patient
            WHERE
                TempPatientKey = {temp_patient_key}
        '''.format(
            temp_patient_key=reserve_row['PatientKey'],
        )
        temp_patient_rows = self.database.select_record(sql)
        if len(temp_patient_rows) <= 0:
            return

        temp_patient_row = temp_patient_rows[0]

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('網路初診預約掛號報到')
        msg_box.setText(
            '''
                <font size="4" color="blue"><b>{name}確定初診預約掛號報到?</b></font><br>
                請確認以下的初診預約資料是否正確:<br><br>
                病患姓名: {name}<br>
                身分證號: {id}<br>
                出生日期: {birthday}<br>
                聯絡電話: {phone_no}<br>
            '''.format(
                name=string_utils.xstr(reserve_row['Name']),
                id=string_utils.xstr(temp_patient_row['ID']),
                birthday=string_utils.xstr(temp_patient_row['Birthday']),
                phone_no=string_utils.xstr(temp_patient_row['PhoneNo']),
            )
        )
        msg_box.setInformativeText("注意！初診預約掛號報到後, 將會新增一筆正式的病患基本資料!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        arrival = msg_box.exec_()
        if not arrival:
            return

        new_patient_key = self._update_new_patient(temp_patient_row)
        reserve_key = reserve_row['ReserveKey']
        sql = '''
            UPDATE reserve
            SET
                PatientKey = {new_patient_key}
            WHERE
                ReserveKey = {reserve_key}
        '''.format(
            new_patient_key=new_patient_key,
            reserve_key=reserve_key,
        )
        self.database.exec_sql(sql)
        self.parent.registration_arrival(reserve_key)

    def _update_new_patient(self, temp_patient_row):
        id = string_utils.xstr(temp_patient_row['ID'])
        gender_code = id[1]
        gender = patient_utils.get_gender(gender_code)

        field = [
            'Name', 'ID', 'Gender', 'Birthday', 'Telephone',
        ]
        data = [
            string_utils.xstr(temp_patient_row['Name']),
            id,
            gender,
            string_utils.xstr(temp_patient_row['Birthday']),
            string_utils.xstr(temp_patient_row['PhoneNo']),
        ]
        new_patient_key = self.database.insert_record('Patient', field, data)

        return new_patient_key

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
        self.ui.comboBox_doctor.setCurrentText(string_utils.xstr(row['Doctor']))
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

    def _reservation_list_changed(self):
        reserve_key = self.table_widget_reservation_list.field_value(0)
        if reserve_key is None:
            return

        arrival = self._check_reservation_arrival(reserve_key)
        if arrival:  # 已報到
            enabled = False
        else:
            enabled = True

        self.ui.action_reservation_arrival.setEnabled(enabled)
        self.ui.action_cancel_reservation.setEnabled(enabled)

